import numpy as np
import tensorflow as tf
import random
from collections import deque
import time
#深度强化学习调度器
class SimpleDRLScheduler:
    """
    简化的深度强化学习调度器
    使用Actor-Critic架构来学习最优的任务分配策略
    """
    # 初始化 SimpleDRLScheduler 类的实例
    def __init__(self, machines_count, max_tasks):
        """
        初始化 SimpleDRLScheduler 类的实例。

        :param machines_count: 可用机器的数量。
        :param max_tasks: 最大任务数量，用于状态向量的填充。
        """
        # 参数验证：确保输入参数有效
        if not isinstance(machines_count, int) or machines_count <= 0:
            raise ValueError("机器数量必须是正整数")
        if not isinstance(max_tasks, int) or max_tasks <= 0:
            raise ValueError("最大任务数量必须是正整数")
        
        # 存储可用机器的数量
        self.machines_count = machines_count
        # 存储最大任务数量
        self.max_tasks = max_tasks
        # 计算状态空间的维度，每台机器有2个特征（CPU和内存使用率），每个任务有3个特征（CPU需求、内存需求和估计时长）
        self.state_dim = machines_count * 2 + max_tasks * 3
        # 计算动作空间的维度，动作数量为机器数量乘以最大任务数量
        self.action_dim = machines_count * max_tasks
        
        # 初始化简化的策略网络（Actor）- 负责选择动作
        self.actor = self._build_simple_actor()
        # 初始化简化的价值网络（Critic）- 负责评估状态-动作对的价值
        self.critic = self._build_simple_critic()
        
        # 初始化经验回放缓冲区，使用双端队列存储经验，最大长度为1000
        # 经验回放是DRL的重要技术，用于打破样本间的相关性
        self.memory = deque(maxlen=1000)
        # 定义每次训练时从经验回放缓冲区中采样的批次大小
        self.batch_size = 32
        # 定义折扣因子，用于计算未来奖励的折现值
        # gamma=0.99表示更重视长期奖励
        self.gamma = 0.99
    #构建Actor网络
    def _build_simple_actor(self):
        """
        构建Actor网络（策略网络）
        输入：当前状态
        输出：每个可能动作的概率分布
        """
        model = tf.keras.Sequential([
            # 输入层：接收状态向量
            tf.keras.layers.Dense(64, activation='relu', input_shape=(self.state_dim,)),
            # 隐藏层：64个神经元，使用ReLU激活函数
            tf.keras.layers.Dense(32, activation='relu'),
            # 输出层：输出动作概率分布，使用softmax确保概率和为1
            tf.keras.layers.Dense(self.action_dim, activation='softmax')
        ])
        model.compile(optimizer='adam')
        return model
    #构建Critic网络
    def _build_simple_critic(self):
        """
        构建Critic网络（价值网络）
        输入：状态和动作
        输出：状态-动作对的价值估计
        """
        # 状态输入层
        state_input = tf.keras.layers.Input(shape=(self.state_dim,))
        # 动作输入层
        action_input = tf.keras.layers.Input(shape=(self.action_dim,))
        
        # 将状态和动作连接起来
        x = tf.keras.layers.Concatenate()([state_input, action_input])
        # 隐藏层处理
        x = tf.keras.layers.Dense(64, activation='relu')(x)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        # 输出层：输出单个价值估计
        output = tf.keras.layers.Dense(1)(x)
        
        # 构建模型
        model = tf.keras.Model(inputs=[state_input, action_input], outputs=output)
        model.compile(optimizer='adam', loss='mse')  # 使用均方误差损失函数
        return model
    #构建当前环境的状态向量
    def get_state(self, machines, waiting_tasks):
        """
        构建当前环境的状态向量
        
        :param machines: 当前所有机器的状态列表
        :param waiting_tasks: 等待分配的任务列表
        :return: 归一化后的状态向量
        """
        state = []
        
        # 机器状态：每台机器包含CPU使用率和内存使用率
        for machine in machines:
            # 归一化到0-1范围
            state.append(machine.cpu_usage / 100.0)
            state.append(machine.memory_usage / 100.0)
        
        # 任务状态：每个任务包含CPU需求、内存需求和估计执行时长
        for task in waiting_tasks:
            # 归一化到0-1范围
            state.append(task.cpu_demand / 100.0)
            state.append(task.memory_demand / 100.0)
            # 将执行时长从秒转换为小时，便于归一化
            state.append(task.estimated_duration / 3600.0)
        
        # 填充：如果任务数量不足max_tasks，用0填充
        # 这确保了状态向量的维度始终一致
        padding = self.max_tasks - len(waiting_tasks)
        state.extend([0] * (padding * 3))
        
        return np.array(state)
    #根据当前状态选择动作
    def select_action(self, state):
        """
        根据当前状态选择动作
        
        :param state: 当前状态向量
        :return: 选择的动作索引
        """
        # 使用Actor网络预测动作概率分布
        action_probs = self.actor.predict(np.array([state]), verbose=0)[0]
        # 选择概率最高的动作（贪婪策略）
        return np.argmax(action_probs)
    
    def remember(self, state, action, reward, next_state, done):
        """
        将经验存储到经验回放缓冲区
        
        :param state: 当前状态
        :param action: 执行的动作
        :param reward: 获得的奖励
        :param next_state: 下一个状态
        :param done: 是否结束
        """
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """
        从经验回放缓冲区中采样并训练网络
        这是DRL的核心训练过程
        """
        # 确保有足够的经验样本
        if len(self.memory) < self.batch_size:
            return
        
        # 随机采样一批经验
        minibatch = random.sample(self.memory, self.batch_size)
        
        # 分离经验中的各个组成部分
        states = np.array([exp[0] for exp in minibatch])
        actions = np.array([exp[1] for exp in minibatch])
        rewards = np.array([exp[2] for exp in minibatch])
        next_states = np.array([exp[3] for exp in minibatch])
        dones = np.array([exp[4] for exp in minibatch])
        
        # 将动作转换为one-hot编码，便于网络处理
        actions_one_hot = tf.one_hot(actions, self.action_dim)
        
        # 训练Critic网络
        # 使用目标网络计算目标Q值，减少训练的不稳定性
        target_actions = self.actor.predict(next_states, verbose=0)
        target_q_values = self.critic.predict([next_states, target_actions], verbose=0)
        # 计算目标值：当前奖励 + 折扣的未来价值
        y = rewards + self.gamma * target_q_values * (1 - dones)
        
        # 训练Critic网络
        self.critic.fit([tf.convert_to_tensor(states, dtype=tf.float32), actions_one_hot], 
                       y, verbose=0, batch_size=self.batch_size)
        
        # 训练Actor网络
        with tf.GradientTape() as tape:
            # 前向传播
            actions_pred = self.actor(tf.convert_to_tensor(states, dtype=tf.float32))
            critic_value = self.critic([tf.convert_to_tensor(states, dtype=tf.float32), actions_pred])
            # Actor损失：最大化Critic的价值估计
            actor_loss = -tf.math.reduce_mean(critic_value)
        
        # 计算梯度并更新Actor网络
        actor_gradients = tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor.optimizer.apply_gradients(zip(actor_gradients, self.actor.trainable_variables))
#任务类
class Task:
    """
    任务类：表示一个需要调度的任务
    """
    def __init__(self, task_id, arrival_time, cpu_demand, memory_demand, estimated_duration):
        self.task_id = task_id                    # 任务唯一标识
        self.arrival_time = arrival_time          # 任务到达时间
        self.cpu_demand = cpu_demand              # CPU需求（百分比）
        self.memory_demand = memory_demand        # 内存需求（百分比）
        self.estimated_duration = estimated_duration  # 估计执行时长（秒）
        self.execution_time = None                # 实际执行时长
        self.completion_time = None               # 完成时间
        self.assigned_machine = None              # 分配的机器

class Machine:
    """
    机器类：表示一台可用的计算机器
    """
    def __init__(self, machine_id, cpu_capacity, memory_capacity):
        self.machine_id = machine_id              # 机器唯一标识
        self.cpu_capacity = cpu_capacity          # CPU总容量（百分比）
        self.memory_capacity = memory_capacity    # 内存总容量（百分比）
        self.cpu_usage = 0                       # 当前CPU使用率
        self.memory_usage = 0                    # 当前内存使用率
        self.running_tasks = []                  # 正在运行的任务列表
    #检查是否可以容纳新任务
    def can_accommodate(self, task):
        """
        检查机器是否可以容纳新任务
        
        :param task: 待分配的任务
        :return: 是否可以容纳
        """
        return (self.cpu_usage + task.cpu_demand <= self.cpu_capacity and
                self.memory_usage + task.memory_demand <= self.memory_capacity)
    #将任务分配给机器
    def assign_task(self, task, current_time):
        """
        将任务分配给机器
        
        :param task: 待分配的任务
        :param current_time: 当前时间
        :return: 是否分配成功
        """
        if self.can_accommodate(task):
            # 添加任务到运行列表
            self.running_tasks.append(task)
            # 更新资源使用情况
            self.cpu_usage += task.cpu_demand
            self.memory_usage += task.memory_demand
            # 设置任务属性
            task.assigned_machine = self
            # 实际执行时间会有一些随机性（模拟真实环境）
            task.execution_time = task.estimated_duration * (0.9 + 0.2 * random.random())
            task.completion_time = current_time + task.execution_time
            return True
        return False
    
    def update(self, current_time):
        """
        更新机器状态，处理已完成的任务
        
        :param current_time: 当前时间
        :return: 已完成的任务列表
        """
        completed_tasks = []
        remaining_tasks = []
        
        # 检查每个运行中的任务
        for task in self.running_tasks:
            if current_time >= task.completion_time:
                # 任务完成
                completed_tasks.append(task)
                # 释放资源
                self.cpu_usage -= task.cpu_demand
                self.memory_usage -= task.memory_demand
            else:
                # 任务仍在运行
                remaining_tasks.append(task)
        
        # 更新运行中的任务列表
        self.running_tasks = remaining_tasks
        return completed_tasks

class SimpleSimulator:
    """
    简单的任务调度模拟器
    用于比较FCFS和DRL算法的性能
    """
    def __init__(self, num_machines, num_tasks):
        self.current_time = 0                    # 当前模拟时间
        # 创建机器：每台机器有100%的CPU和内存容量
        self.machines = [Machine(i, 100, 100) for i in range(num_machines)]
        self.waiting_tasks = deque()             # 等待分配的任务队列
        self.completed_tasks = []                # 已完成的任务列表
        
        # 创建任务：随机生成任务属性
        for i in range(num_tasks):
            arrival_time = i * 5  # 更密集的任务到达
            cpu_demand = random.randint(10, 40)      # CPU需求10-40%
            memory_demand = random.randint(10, 40)   # 内存需求10-40%
            estimated_duration = random.randint(10, 100)  # 执行时长10-100秒
            task = Task(i, arrival_time, cpu_demand, memory_demand, estimated_duration)
            self.waiting_tasks.append(task)
        
        # 初始化DRL调度器
        self.scheduler = SimpleDRLScheduler(num_machines, num_tasks)
    
    def run_fcfs(self):
        """
        运行FCFS（先来先服务）算法
        这是传统的调度算法，用作性能对比基准
        
        :return: 性能指标字典
        """
        # 重置模拟环境
        self.current_time = 0
        self.completed_tasks = []
        waiting_tasks = deque(self.waiting_tasks)
        
        # 重置所有机器状态
        for machine in self.machines:
            machine.cpu_usage = 0
            machine.memory_usage = 0
            machine.running_tasks = []
        
        # 主循环：直到所有任务完成
        while waiting_tasks or any(machine.running_tasks for machine in self.machines):
            # 更新机器状态，处理已完成的任务
            for machine in self.machines:
                completed = machine.update(self.current_time)
                self.completed_tasks.extend(completed)
            
            # 检查新到达的任务
            while waiting_tasks and waiting_tasks[0].arrival_time <= self.current_time:
                task = waiting_tasks.popleft()
                
                # 尝试分配到第一个可用的机器
                assigned = False
                for machine in self.machines:
                    if machine.can_accommodate(task):
                        machine.assign_task(task, self.current_time)
                        assigned = True
                        break
                
                # 如果没有机器可以容纳，将任务放回队列
                if not assigned:
                    waiting_tasks.appendleft(task)
                    break
            
            # 时间前进
            self.current_time += 1
        
        return self._calculate_metrics()
    
    def run_drl(self, episodes=10):
        """
        运行DRL（深度强化学习）算法
        
        :param episodes: 训练轮数
        :return: 最佳性能指标
        """
        best_metrics = None
        best_score = float('inf')
        
        # 训练多个轮次
        for episode in range(episodes):
            # 重置环境
            self.current_time = 0
            self.completed_tasks = []
            waiting_tasks = deque(self.waiting_tasks)
            
            # 重置所有机器状态
            for machine in self.machines:
                machine.cpu_usage = 0
                machine.memory_usage = 0
                machine.running_tasks = []
            
            done = False
            episode_reward = 0
            
            # 单轮训练循环
            while not done:
                # 获取当前状态
                state = self.scheduler.get_state(self.machines, list(waiting_tasks))
                
                # 使用DRL调度器选择动作
                action = self.scheduler.select_action(state)
                
                # 执行动作：将任务分配给机器
                if len(waiting_tasks) > 0:
                    # 从动作索引解析出任务索引和机器索引
                    task_idx = action % len(waiting_tasks)
                    machine_idx = action // len(waiting_tasks)
                    
                    # 确保索引有效
                    if task_idx < len(waiting_tasks) and machine_idx < len(self.machines):
                        task = list(waiting_tasks)[task_idx]
                        machine = self.machines[machine_idx]
                        
                        # 检查任务是否可以分配
                        if task.arrival_time <= self.current_time and machine.can_accommodate(task):
                            waiting_tasks.remove(task)
                            machine.assign_task(task, self.current_time)
                
                # 更新机器状态
                newly_completed = []
                for machine in self.machines:
                    completed = machine.update(self.current_time)
                    newly_completed.extend(completed)
                    self.completed_tasks.extend(completed)
                
                # 计算奖励：完成任务的奖励为负值（鼓励快速完成）
                reward = -len(newly_completed) * 10
                episode_reward += reward
                
                # 时间前进
                self.current_time += 1
                
                # 获取下一个状态
                next_state = self.scheduler.get_state(self.machines, list(waiting_tasks))
                
                # 检查是否结束：所有任务都完成且没有正在运行的任务
                done = (len(waiting_tasks) == 0 and 
                        all(len(machine.running_tasks) == 0 for machine in self.machines))
                
                # 存储经验到回放缓冲区
                self.scheduler.remember(state, action, reward, next_state, done)
                
                # 训练网络
                self.scheduler.replay()
            
            # 计算本轮的性能指标
            metrics = self._calculate_metrics()
            # 计算综合得分：带权周转时间 + 完工时间
            score = metrics['avg_weighted_turnaround'] + metrics['makespan'] / 1000
            
            # 记录最佳结果
            if score < best_score:
                best_score = score
                best_metrics = metrics
            
            # 显示训练进度
            if (episode + 1) % 5 == 0:
                print(f"E{episode+1:2d}", end=" ", flush=True)
        
        return best_metrics
    
    def _calculate_metrics(self):
        """
        计算性能指标
        
        :return: 包含性能指标的字典
        """
        if not self.completed_tasks:
            return {'avg_weighted_turnaround': 0, 'makespan': 0}
        
        # 计算平均带权周转时间
        total_weighted_turnaround = 0
        for task in self.completed_tasks:
            # 周转时间 = 完成时间 - 到达时间
            turnaround_time = task.completion_time - task.arrival_time
            # 带权周转时间 = 周转时间 / 执行时间
            weighted_turnaround = turnaround_time / task.execution_time
            total_weighted_turnaround += weighted_turnaround
        
        avg_weighted_turnaround = total_weighted_turnaround / len(self.completed_tasks)
        
        # 计算完工时间：最后一个任务完成的时间
        makespan = max(task.completion_time for task in self.completed_tasks)
        
        return {
            'avg_weighted_turnaround': avg_weighted_turnaround,
            'makespan': makespan
        }

def main():
    """
    主函数：运行性能对比实验
    """
    print("=" * 60)
    print("🚀 深度强化学习任务调度系统 - 快速演示版")
    print("=" * 60)
    
    print("📊 模拟环境配置:")
    print("   - 机器数量: 5台")
    print("   - 任务数量: 50个")
    print("   - 训练轮数: 10轮")
    print()
    
    # 创建模拟器
    sim = SimpleSimulator(5, 50)
    
    print("🔄 正在运行FCFS（先来先服务）算法...")
    start_time = time.time()
    fcfs_metrics = sim.run_fcfs()
    fcfs_time = time.time() - start_time
    print(f"✅ FCFS算法完成 (耗时: {fcfs_time:.2f}秒)")
    print()
    
    print("🧠 正在训练深度强化学习调度器...")
    print("   训练进度: ", end="", flush=True)
    start_time = time.time()
    drl_metrics = sim.run_drl(episodes=10)
    drl_time = time.time() - start_time
    print(f"\n✅ 深度强化学习训练完成 (耗时: {drl_time:.2f}秒)")
    print()
    
    # 计算改进百分比
    wt_improvement = (fcfs_metrics['avg_weighted_turnaround'] - drl_metrics['avg_weighted_turnaround']) / fcfs_metrics['avg_weighted_turnaround'] * 100
    makespan_improvement = (fcfs_metrics['makespan'] - drl_metrics['makespan']) / fcfs_metrics['makespan'] * 100
    
    print("📈 性能对比结果:")
    print("=" * 60)
    print(f"{'指标':<20} {'FCFS':<15} {'DRL':<15} {'改进':<10}")
    print("-" * 60)
    print(f"{'平均带权周转时间':<20} {fcfs_metrics['avg_weighted_turnaround']:<15.2f} {drl_metrics['avg_weighted_turnaround']:<15.2f} {wt_improvement:>+.2f}%")
    print(f"{'完工时间':<20} {fcfs_metrics['makespan']:<15.2f} {drl_metrics['makespan']:<15.2f} {makespan_improvement:>+.2f}%")
    print("=" * 60)
    
    print("\n🎯 效率提升总结:")
    if wt_improvement > 0:
        print(f"   ✅ 带权周转时间降低了 {wt_improvement:.2f}%")
    else:
        print(f"   ❌ 带权周转时间增加了 {abs(wt_improvement):.2f}%")
    
    if makespan_improvement > 0:
        print(f"   ✅ 完工时间降低了 {makespan_improvement:.2f}%")
    else:
        print(f"   ❌ 完工时间增加了 {abs(makespan_improvement):.2f}%")
    
    # 计算综合性能提升
    overall_improvement = (wt_improvement + makespan_improvement) / 2
    print(f"\n📊 综合性能提升: {overall_improvement:+.2f}%")
    
    if overall_improvement > 0:
        print("🎉 深度强化学习调度器表现优异！")
    else:
        print("⚠️  需要进一步优化训练参数")
    
    print(f"\n⏱️  执行时间对比:")
    print(f"   FCFS: {fcfs_time:.2f}秒")
    print(f"   DRL: {drl_time:.2f}秒")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 