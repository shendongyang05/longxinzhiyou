"""
深度强化学习任务调度器测试模块

本模块包含对SimpleDRLScheduler类的全面测试，确保：
1. 初始化参数验证
2. 神经网络结构正确性
3. 状态和动作空间维度计算
4. 边界条件处理

作者: 系统开发团队
创建时间: 2025年
"""

import unittest
import numpy as np
import tensorflow as tf
from collections import deque
# 导入待测试的调度器类
from KylinTuningSystem.KylinTuningSystem.demo import SimpleDRLScheduler

class TestSimpleDRLSchedulerInit(unittest.TestCase):
    """
    测试SimpleDRLScheduler类的初始化功能
    
    测试覆盖：
    - 正常参数初始化
    - 边界条件处理
    - 神经网络结构验证
    - 超参数设置
    """
    
    def setUp(self):
        """
        在每个测试方法前执行的初始化方法
        
        设置测试环境：
        - machines_count: 测试用的机器数量
        - max_tasks: 测试用的最大任务数量
        """
        self.machines_count = 3    # 3台机器用于测试
        self.max_tasks = 5         # 最多5个任务
    
    def test_init_with_valid_params(self):
        """
        测试用有效参数初始化调度器
        
        验证内容：
        1. 基本属性设置正确
        2. 状态和动作维度计算准确
        3. 神经网络模型正确创建
        4. 经验回放缓冲区配置正确
        5. 超参数设置合理
        """
        # 创建调度器实例
        scheduler = SimpleDRLScheduler(self.machines_count, self.max_tasks)
        
        # 验证基本属性设置
        self.assertEqual(scheduler.machines_count, self.machines_count, 
                        "机器数量设置不正确")
        self.assertEqual(scheduler.max_tasks, self.max_tasks, 
                        "最大任务数量设置不正确")
        
        # 验证状态和动作维度计算
        # 状态维度 = 机器数量×2(CPU+内存) + 最大任务数×3(CPU需求+内存需求+执行时长)
        expected_state_dim = self.machines_count * 2 + self.max_tasks * 3
        # 动作维度 = 机器数量 × 最大任务数
        expected_action_dim = self.machines_count * self.max_tasks
        
        self.assertEqual(scheduler.state_dim, expected_state_dim, 
                        "状态空间维度计算错误")
        self.assertEqual(scheduler.action_dim, expected_action_dim, 
                        "动作空间维度计算错误")
        
        # 验证神经网络模型是否正确创建
        self.assertIsInstance(scheduler.actor, tf.keras.Model, 
                             "Actor网络应该是一个Keras模型")
        self.assertIsInstance(scheduler.critic, tf.keras.Model, 
                             "Critic网络应该是一个Keras模型")
        
        # 验证经验回放缓冲区配置
        self.assertIsInstance(scheduler.memory, deque, 
                             "经验回放缓冲区应该是双端队列")
        self.assertEqual(scheduler.memory.maxlen, 1000, 
                        "经验回放缓冲区最大长度应该是1000")
        
        # 验证超参数设置
        self.assertEqual(scheduler.batch_size, 32, 
                        "批次大小应该是32")
        self.assertEqual(scheduler.gamma, 0.99, 
                        "折扣因子应该是0.99")
    
    def test_init_with_zero_machines(self):
        """
        测试机器数量为0时的初始化
        
        预期行为：应该抛出ValueError异常
        原因：没有机器就无法进行任务调度
        """
        with self.assertRaises(ValueError):
            SimpleDRLScheduler(0, self.max_tasks)
    
    def test_init_with_negative_machines(self):
        """
        测试机器数量为负数时的初始化
        
        预期行为：应该抛出ValueError异常
        原因：机器数量不能为负数
        """
        with self.assertRaises(ValueError):
            SimpleDRLScheduler(-1, self.max_tasks)
    
    def test_init_with_zero_tasks(self):
        """
        测试任务数量为0时的初始化
        
        预期行为：应该抛出ValueError异常
        原因：没有任务就不需要调度
        """
        with self.assertRaises(ValueError):
            SimpleDRLScheduler(self.machines_count, 0)
    
    def test_init_with_negative_tasks(self):
        """
        测试任务数量为负数时的初始化
        
        预期行为：应该抛出ValueError异常
        原因：任务数量不能为负数
        """
        with self.assertRaises(ValueError):
            SimpleDRLScheduler(self.machines_count, -1)
    
    def test_init_with_large_numbers(self):
        """
        测试用大数字初始化调度器
        
        验证内容：
        1. 大数字情况下维度计算仍然正确
        2. 系统能够处理大规模场景
        3. 数值溢出问题处理
        """
        large_machines = 1000      # 1000台机器
        large_tasks = 10000        # 10000个任务
        
        # 创建大规模调度器
        scheduler = SimpleDRLScheduler(large_machines, large_tasks)
        
        # 验证维度计算是否正确
        expected_state_dim = large_machines * 2 + large_tasks * 3
        expected_action_dim = large_machines * large_tasks
        
        self.assertEqual(scheduler.state_dim, expected_state_dim, 
                        "大规模场景下状态空间维度计算错误")
        self.assertEqual(scheduler.action_dim, expected_action_dim, 
                        "大规模场景下动作空间维度计算错误")
    
    def test_actor_network_structure(self):
        """
        验证Actor网络结构
        
        验证内容：
        1. 输入层维度与状态空间匹配
        2. 输出层维度与动作空间匹配
        3. 网络结构符合预期设计
        """
        scheduler = SimpleDRLScheduler(self.machines_count, self.max_tasks)
        actor = scheduler.actor
        
        # 验证输入层：应该只有一个输入，维度为状态空间维度
        self.assertEqual(len(actor.inputs), 1, 
                        "Actor网络应该只有一个输入")
        self.assertEqual(actor.inputs[0].shape[1], scheduler.state_dim, 
                        "Actor网络输入维度应该与状态空间维度匹配")
        
        # 验证输出层：应该只有一个输出，维度为动作空间维度
        self.assertEqual(len(actor.outputs), 1, 
                        "Actor网络应该只有一个输出")
        self.assertEqual(actor.outputs[0].shape[1], scheduler.action_dim, 
                        "Actor网络输出维度应该与动作空间维度匹配")
    
    def test_critic_network_structure(self):
        """
        验证Critic网络结构
        
        验证内容：
        1. 输入层包含状态和动作两个输入
        2. 输入维度计算正确
        3. 输出层为单个价值估计
        """
        scheduler = SimpleDRLScheduler(self.machines_count, self.max_tasks)
        critic = scheduler.critic
        
        # 验证输入层：应该有两个输入（状态+动作）
        self.assertEqual(len(critic.inputs), 2, 
                        "Critic网络应该有两个输入（状态和动作）")
        
        # 验证输入维度：状态维度 + 动作维度
        expected_input_dim = scheduler.state_dim + scheduler.action_dim
        self.assertEqual(critic.inputs[0].shape[1], scheduler.state_dim, 
                        "Critic网络状态输入维度错误")
        self.assertEqual(critic.inputs[1].shape[1], scheduler.action_dim, 
                        "Critic网络动作输入维度错误")
        
        # 验证输出层：应该只有一个输出，维度为1（价值估计）
        self.assertEqual(len(critic.outputs), 1, 
                        "Critic网络应该只有一个输出")
        self.assertEqual(critic.outputs[0].shape[1], 1, 
                        "Critic网络输出应该是单个价值估计")

if __name__ == '__main__':
    """
    测试入口点
    
    运行方式：
    python test.py
    
    或者使用unittest模块：
    python -m unittest test.py -v
    """
    # 运行所有测试用例
    unittest.main(verbosity=2)
