import numpy as np
import tensorflow as tf
import random
from collections import deque

class DeepRLScheduler:
    def __init__(self, machines_count, max_tasks, state_dim, action_dim):
        self.machines_count = machines_count  # 机器数量
        self.max_tasks = max_tasks  # 最大任务数
        self.state_dim = state_dim  # 状态空间维度
        self.action_dim = action_dim  # 动作空间维度
        
        # 经验回放缓冲区
        self.memory = deque(maxlen=10000)
        
        # 创建Actor和Critic网络
        self.actor = self._build_actor()
        self.critic = self._build_critic()
        
        # 目标网络
        self.target_actor = self._build_actor()
        self.target_critic = self._build_critic()
        
        # 初始化目标网络权重
        self.target_actor.set_weights(self.actor.get_weights())
        self.target_critic.set_weights(self.critic.get_weights())
        
        # 超参数
        self.gamma = 0.99  # 折扣因子
        self.tau = 0.001   # 软更新参数
        self.batch_size = 64
        
    def _build_actor(self):
        """构建Actor网络，用于生成动作"""
        inputs = tf.keras.layers.Input(shape=(self.state_dim,))
        x = tf.keras.layers.Dense(256, activation='relu')(inputs)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        outputs = tf.keras.layers.Dense(self.action_dim, activation='softmax')(x)
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=tf.keras.optimizers.Adam(0.001))
        return model
    
    def _build_critic(self):
        """构建Critic网络，用于评估动作价值"""
        state_input = tf.keras.layers.Input(shape=(self.state_dim,))
        action_input = tf.keras.layers.Input(shape=(self.action_dim,))
        
        x = tf.keras.layers.Concatenate()([state_input, action_input])
        x = tf.keras.layers.Dense(256, activation='relu')(x)
        x = tf.keras.layers.Dense(128, activation='relu')(x)
        outputs = tf.keras.layers.Dense(1)(x)
        
        model = tf.keras.Model(inputs=[state_input, action_input], outputs=outputs)
        model.compile(optimizer=tf.keras.optimizers.Adam(0.002), loss='mse')
        return model
    
    def get_state(self, machines, waiting_tasks):
        """构造系统当前状态
        包括：机器运行状态、等待任务状态、积压队列状态等
        """
        state = []
        
        # 添加机器状态信息
        for machine in machines:
            # 归一化的CPU利用率
            state.append(machine.cpu_usage / 100.0)
            # 归一化的内存利用率
            state.append(machine.memory_usage / 100.0)
        
        # 添加等待任务信息
        for task in waiting_tasks:
            # 归一化的任务CPU需求
            state.append(task.cpu_demand / 100.0)
            # 归一化的任务内存需求
            state.append(task.memory_demand / 100.0)
            # 归一化的任务预计执行时间
            state.append(task.estimated_duration / 3600.0)
        
        # 如果等待任务不足，用0填充
        padding = self.max_tasks - len(waiting_tasks)
        state.extend([0] * (padding * 3))
        
        return np.array(state)
    
    def select_action(self, state):
        """根据当前状态选择动作"""
        action_probs = self.actor.predict(np.array([state]))[0]
        return np.argmax(action_probs)
    
    def calculate_reward(self, completed_tasks, current_time):
        """计算奖励函数
        r = -∑(t/d_j)，其中t为两次调度间隔，d_j为任务j的实际执行时间
        """
        total_weighted_turnaround = 0
        
        for task in completed_tasks:
            # 计算任务的带权周转时间
            turnaround_time = task.completion_time - task.arrival_time
            weighted_turnaround = turnaround_time / task.execution_time
            total_weighted_turnaround += weighted_turnaround
        
        # 负值作为奖励，因为我们要最小化带权周转时间
        reward = -total_weighted_turnaround
        return reward
    
    def remember(self, state, action, reward, next_state, done):
        """存储经验到回放缓冲区"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """从经验回放缓冲区中采样并训练网络"""
        if len(self.memory) < self.batch_size:
            return
        
        # 随机采样
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.array([experience[0] for experience in minibatch])
        actions = np.array([experience[1] for experience in minibatch])
        rewards = np.array([experience[2] for experience in minibatch])
        next_states = np.array([experience[3] for experience in minibatch])
        dones = np.array([experience[4] for experience in minibatch])
        
        # 更新Critic
        target_actions = self.target_actor.predict(next_states)
        target_q_values = self.target_critic.predict([next_states, target_actions])
        
        y = rewards + self.gamma * target_q_values * (1 - dones)
        self.critic.fit([states, actions], y, verbose=0)
        
        # 更新Actor
        with tf.GradientTape() as tape:
            actions = self.actor(states)
            critic_value = self.critic([states, actions])
            actor_loss = -tf.math.reduce_mean(critic_value)
        
        actor_gradients = tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor.optimizer.apply_gradients(zip(actor_gradients, self.actor.trainable_variables))
        
        # 软更新目标网络
        self._update_target_networks()
    
    def _update_target_networks(self):
        """软更新目标网络"""
        actor_weights = self.actor.get_weights()
        target_actor_weights = self.target_actor.get_weights()
        critic_weights = self.critic.get_weights()
        target_critic_weights = self.target_critic.get_weights()
        
        for i in range(len(actor_weights)):
            target_actor_weights[i] = self.tau * actor_weights[i] + (1 - self.tau) * target_actor_weights[i]
        
        for i in range(len(critic_weights)):
            target_critic_weights[i] = self.tau * critic_weights[i] + (1 - self.tau) * target_critic_weights[i]
        
        self.target_actor.set_weights(target_actor_weights)
        self.target_critic.set_weights(target_critic_weights)


class Task:
    def __init__(self, task_id, arrival_time, cpu_demand, memory_demand, estimated_duration):
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.cpu_demand = cpu_demand
        self.memory_demand = memory_demand
        self.estimated_duration = estimated_duration
        self.execution_time = None  # 实际执行时间，调度后确定
        self.completion_time = None  # 完成时间
        self.assigned_machine = None  # 分配的机器


class Machine:
    def __init__(self, machine_id, cpu_capacity, memory_capacity):
        self.machine_id = machine_id
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity
        self.cpu_usage = 0
        self.memory_usage = 0
        self.running_tasks = []
    
    def can_accommodate(self, task):
        """检查机器是否能容纳任务"""
        return (self.cpu_usage + task.cpu_demand <= self.cpu_capacity and
                self.memory_usage + task.memory_demand <= self.memory_capacity)
    
    def assign_task(self, task, current_time):
        """分配任务到机器"""
        if self.can_accommodate(task):
            self.running_tasks.append(task)
            self.cpu_usage += task.cpu_demand
            self.memory_usage += task.memory_demand
            task.assigned_machine = self
            # 设置实际执行时间（可以加入一些随机性模拟实际环境）
            task.execution_time = task.estimated_duration * (0.9 + 0.2 * random.random())
            task.completion_time = current_time + task.execution_time
            return True
        return False
    
    def update(self, current_time):
        """更新机器状态，移除已完成的任务"""
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


class Simulator:
    def __init__(self, num_machines, num_tasks):
        self.current_time = 0
        self.machines = [Machine(i, 100, 100) for i in range(num_machines)]
        self.waiting_tasks = deque()
        self.completed_tasks = []
        
        # 创建任务
        for i in range(num_tasks):
            arrival_time = i * 10  # 简化：每10个时间单位到达一个任务
            cpu_demand = random.randint(10, 50)
            memory_demand = random.randint(10, 50)
            estimated_duration = random.randint(20, 200)
            task = Task(i, arrival_time, cpu_demand, memory_demand, estimated_duration)
            self.waiting_tasks.append(task)
        
        # 初始化调度器
        state_dim = num_machines * 2 + num_tasks * 3  # 机器状态 + 任务状态
        action_dim = num_machines * num_tasks  # 简化：每个动作对应将一个任务分配到一个机器
        self.scheduler = DeepRLScheduler(num_machines, num_tasks, state_dim, action_dim)
    
    def run_fcfs(self):
        """运行先来先服务(FCFS)算法进行对比"""
        self.current_time = 0
        self.completed_tasks = []
        
        # 复制等待任务队列
        waiting_tasks = deque(self.waiting_tasks)
        
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
                
                # 如果无法分配，放回队列头部
                if not assigned:
                    waiting_tasks.appendleft(task)
                    break
            
            # 时间前进
            self.current_time += 1
        
        # 计算评价指标
        avg_weighted_turnaround = self._calculate_avg_weighted_turnaround()
        makespan = self._calculate_makespan()
        
        return avg_weighted_turnaround, makespan
    
    def run_drl(self, episodes=100):
        """运行深度强化学习调度算法"""
        best_avg_weighted_turnaround = float('inf')
        best_makespan = float('inf')
        
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
                # 获取当前状态
                state = self.scheduler.get_state(self.machines, list(waiting_tasks))
                
                # 选择动作
                action = self.scheduler.select_action(state)
                
                # 执行动作
                task_idx = action % len(waiting_tasks)
                machine_idx = action // len(waiting_tasks)
                
                if task_idx < len(waiting_tasks) and machine_idx < len(self.machines):
                    task = list(waiting_tasks)[task_idx]
                    machine = self.machines[machine_idx]
                    
                    if task.arrival_time <= self.current_time and machine.can_accommodate(task):
                        # 从等待队列中移除任务
                        waiting_tasks.remove(task)
                        # 分配任务到机器
                        machine.assign_task(task, self.current_time)
                
                # 更新所有机器状态
                newly_completed = []
                for machine in self.machines:
                    completed = machine.update(self.current_time)
                    newly_completed.extend(completed)
                    self.completed_tasks.extend(completed)
                
                # 计算奖励
                reward = self.scheduler.calculate_reward(newly_completed, self.current_time)
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
            
            # 计算评价指标
            avg_weighted_turnaround = self._calculate_avg_weighted_turnaround()
            makespan = self._calculate_makespan()
            
            # 更新最佳结果
            if avg_weighted_turnaround < best_avg_weighted_turnaround:
                best_avg_weighted_turnaround = avg_weighted_turnaround
            
            if makespan < best_makespan:
                best_makespan = makespan
            
            print(f"Episode {episode}: Avg Weighted Turnaround = {avg_weighted_turnaround:.2f}, Makespan = {makespan:.2f}")
        
        return best_avg_weighted_turnaround, best_makespan
    
    def _calculate_avg_weighted_turnaround(self):
        """计算平均带权周转时间"""
        if not self.completed_tasks:
            return 0
        
        total_weighted_turnaround = 0
        for task in self.completed_tasks:
            turnaround_time = task.completion_time - task.arrival_time
            weighted_turnaround = turnaround_time / task.execution_time
            total_weighted_turnaround += weighted_turnaround
        
        return total_weighted_turnaround / len(self.completed_tasks)
    
    def _calculate_makespan(self):
        """计算完工时间"""
        if not self.completed_tasks:
            return 0
        
        return max(task.completion_time for task in self.completed_tasks)


# 使用示例
if __name__ == "__main__":
    # 创建模拟环境：10台机器，100个任务
    sim = Simulator(10, 100)
    
    # 运行先来先服务算法
    fcfs_wt, fcfs_makespan = sim.run_fcfs()
    print(f"FCFS: Avg Weighted Turnaround = {fcfs_wt:.2f}, Makespan = {fcfs_makespan:.2f}")
    
    # 运行深度强化学习算法
    drl_wt, drl_makespan = sim.run_drl(episodes=50)
    print(f"DRL: Avg Weighted Turnaround = {drl_wt:.2f}, Makespan = {drl_makespan:.2f}")
    
    # 计算改进百分比
    wt_improvement = (fcfs_wt - drl_wt) / fcfs_wt * 100
    makespan_improvement = (fcfs_makespan - drl_makespan) / fcfs_makespan * 100
    
    print(f"带权周转时间降低: {wt_improvement:.2f}%")
    print(f"完工时间降低: {makespan_improvement:.2f}%")
