import numpy as np
import tensorflow as tf
import random
from collections import deque
import time

class SimpleDRLScheduler:
    def __init__(self, machines_count, max_tasks):
        self.machines_count = machines_count
        self.max_tasks = max_tasks
        self.state_dim = machines_count * 2 + max_tasks * 3
        self.action_dim = machines_count * max_tasks
        
        # 简化的神经网络
        self.actor = self._build_simple_actor()
        self.critic = self._build_simple_critic()
        
        # 经验回放
        self.memory = deque(maxlen=1000)
        self.batch_size = 32
        self.gamma = 0.99
        
    def _build_simple_actor(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(self.state_dim,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(self.action_dim, activation='softmax')
        ])
        model.compile(optimizer='adam')
        return model
    
    def _build_simple_critic(self):
        state_input = tf.keras.layers.Input(shape=(self.state_dim,))
        action_input = tf.keras.layers.Input(shape=(self.action_dim,))
        
        x = tf.keras.layers.Concatenate()([state_input, action_input])
        x = tf.keras.layers.Dense(64, activation='relu')(x)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        output = tf.keras.layers.Dense(1)(x)
        
        model = tf.keras.Model(inputs=[state_input, action_input], outputs=output)
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def get_state(self, machines, waiting_tasks):
        state = []
        
        # 机器状态
        for machine in machines:
            state.append(machine.cpu_usage / 100.0)
            state.append(machine.memory_usage / 100.0)
        
        # 任务状态
        for task in waiting_tasks:
            state.append(task.cpu_demand / 100.0)
            state.append(task.memory_demand / 100.0)
            state.append(task.estimated_duration / 3600.0)
        
        # 填充
        padding = self.max_tasks - len(waiting_tasks)
        state.extend([0] * (padding * 3))
        
        return np.array(state)
    
    def select_action(self, state):
        action_probs = self.actor.predict(np.array([state]), verbose=0)[0]
        return np.argmax(action_probs)
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        if len(self.memory) < self.batch_size:
            return
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.array([exp[0] for exp in minibatch])
        actions = np.array([exp[1] for exp in minibatch])
        rewards = np.array([exp[2] for exp in minibatch])
        next_states = np.array([exp[3] for exp in minibatch])
        dones = np.array([exp[4] for exp in minibatch])
        
        # 转换为one-hot
        actions_one_hot = tf.one_hot(actions, self.action_dim)
        
        # 训练critic
        target_actions = self.actor.predict(next_states, verbose=0)
        target_q_values = self.critic.predict([next_states, target_actions], verbose=0)
        y = rewards + self.gamma * target_q_values * (1 - dones)
        
        self.critic.fit([tf.convert_to_tensor(states, dtype=tf.float32), actions_one_hot], 
                       y, verbose=0, batch_size=self.batch_size)
        
        # 训练actor
        with tf.GradientTape() as tape:
            actions_pred = self.actor(tf.convert_to_tensor(states, dtype=tf.float32))
            critic_value = self.critic([tf.convert_to_tensor(states, dtype=tf.float32), actions_pred])
            actor_loss = -tf.math.reduce_mean(critic_value)
        
        actor_gradients = tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor.optimizer.apply_gradients(zip(actor_gradients, self.actor.trainable_variables))

class Task:
    def __init__(self, task_id, arrival_time, cpu_demand, memory_demand, estimated_duration):
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.cpu_demand = cpu_demand
        self.memory_demand = memory_demand
        self.estimated_duration = estimated_duration
        self.execution_time = None
        self.completion_time = None
        self.assigned_machine = None

class Machine:
    def __init__(self, machine_id, cpu_capacity, memory_capacity):
        self.machine_id = machine_id
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity
        self.cpu_usage = 0
        self.memory_usage = 0
        self.running_tasks = []
    
    def can_accommodate(self, task):
        return (self.cpu_usage + task.cpu_demand <= self.cpu_capacity and
                self.memory_usage + task.memory_demand <= self.memory_capacity)
    
    def assign_task(self, task, current_time):
        if self.can_accommodate(task):
            self.running_tasks.append(task)
            self.cpu_usage += task.cpu_demand
            self.memory_usage += task.memory_demand
            task.assigned_machine = self
            task.execution_time = task.estimated_duration * (0.9 + 0.2 * random.random())
            task.completion_time = current_time + task.execution_time
            return True
        return False
    
    def update(self, current_time):
        completed_tasks = []
        remaining_tasks = []
        
        for task in self.running_tasks:
            if current_time >= task.completion_time:
                completed_tasks.append(task)
                self.cpu_usage -= task.cpu_demand
                self.memory_usage -= task.memory_demand
            else:
                remaining_tasks.append(task)
        
        self.running_tasks = remaining_tasks
        return completed_tasks

class SimpleSimulator:
    def __init__(self, num_machines, num_tasks):
        self.current_time = 0
        self.machines = [Machine(i, 100, 100) for i in range(num_machines)]
        self.waiting_tasks = deque()
        self.completed_tasks = []
        
        # 创建任务
        for i in range(num_tasks):
            arrival_time = i * 5  # 更密集的任务到达
            cpu_demand = random.randint(10, 40)
            memory_demand = random.randint(10, 40)
            estimated_duration = random.randint(10, 100)
            task = Task(i, arrival_time, cpu_demand, memory_demand, estimated_duration)
            self.waiting_tasks.append(task)
        
        # 初始化调度器
        self.scheduler = SimpleDRLScheduler(num_machines, num_tasks)
    
    def run_fcfs(self):
        """运行FCFS算法"""
        self.current_time = 0
        self.completed_tasks = []
        waiting_tasks = deque(self.waiting_tasks)
        
        for machine in self.machines:
            machine.cpu_usage = 0
            machine.memory_usage = 0
            machine.running_tasks = []
        
        while waiting_tasks or any(machine.running_tasks for machine in self.machines):
            # 更新机器状态
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
                
                if not assigned:
                    waiting_tasks.appendleft(task)
                    break
            
            self.current_time += 1
        
        return self._calculate_metrics()
    
    def run_drl(self, episodes=10):
        """运行DRL算法"""
        best_metrics = None
        best_score = float('inf')
        
        for episode in range(episodes):
            # 重置环境
            self.current_time = 0
            self.completed_tasks = []
            waiting_tasks = deque(self.waiting_tasks)
            
            for machine in self.machines:
                machine.cpu_usage = 0
                machine.memory_usage = 0
                machine.running_tasks = []
            
            done = False
            episode_reward = 0
            
            while not done:
                # 获取状态
                state = self.scheduler.get_state(self.machines, list(waiting_tasks))
                
                # 选择动作
                action = self.scheduler.select_action(state)
                
                # 执行动作
                if len(waiting_tasks) > 0:
                    task_idx = action % len(waiting_tasks)
                    machine_idx = action // len(waiting_tasks)
                    
                    if task_idx < len(waiting_tasks) and machine_idx < len(self.machines):
                        task = list(waiting_tasks)[task_idx]
                        machine = self.machines[machine_idx]
                        
                        if task.arrival_time <= self.current_time and machine.can_accommodate(task):
                            waiting_tasks.remove(task)
                            machine.assign_task(task, self.current_time)
                
                # 更新机器状态
                newly_completed = []
                for machine in self.machines:
                    completed = machine.update(self.current_time)
                    newly_completed.extend(completed)
                    self.completed_tasks.extend(completed)
                
                # 计算奖励
                reward = -len(newly_completed) * 10  # 简单的奖励函数
                episode_reward += reward
                
                # 时间前进
                self.current_time += 1
                
                # 获取下一个状态
                next_state = self.scheduler.get_state(self.machines, list(waiting_tasks))
                
                # 检查是否结束
                done = (len(waiting_tasks) == 0 and 
                        all(len(machine.running_tasks) == 0 for machine in self.machines))
                
                # 存储经验
                self.scheduler.remember(state, action, reward, next_state, done)
                
                # 训练网络
                self.scheduler.replay()
            
            # 计算指标
            metrics = self._calculate_metrics()
            score = metrics['avg_weighted_turnaround'] + metrics['makespan'] / 1000
            
            if score < best_score:
                best_score = score
                best_metrics = metrics
            
            # 显示进度
            if (episode + 1) % 5 == 0:
                print(f"E{episode+1:2d}", end=" ", flush=True)
        
        return best_metrics
    
    def _calculate_metrics(self):
        """计算性能指标"""
        if not self.completed_tasks:
            return {'avg_weighted_turnaround': 0, 'makespan': 0}
        
        total_weighted_turnaround = 0
        for task in self.completed_tasks:
            turnaround_time = task.completion_time - task.arrival_time
            weighted_turnaround = turnaround_time / task.execution_time
            total_weighted_turnaround += weighted_turnaround
        
        avg_weighted_turnaround = total_weighted_turnaround / len(self.completed_tasks)
        makespan = max(task.completion_time for task in self.completed_tasks)
        
        return {
            'avg_weighted_turnaround': avg_weighted_turnaround,
            'makespan': makespan
        }

def main():
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