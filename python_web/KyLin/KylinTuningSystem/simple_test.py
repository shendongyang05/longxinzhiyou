"""
简化版深度强化学习任务调度器测试

本文件直接测试demo.py中的功能，避免复杂的模块导入问题。
主要用于验证核心功能的正确性。

运行方式：
python simple_test.py
"""

import sys
import os

# 添加当前目录到Python路径，确保可以导入demo模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from demo import SimpleDRLScheduler, Task, Machine, SimpleSimulator
    print("✅ 成功导入所需模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保demo.py文件在当前目录中")
    sys.exit(1)

def test_scheduler_initialization():
    """测试调度器初始化"""
    print("\n🧪 测试1: 调度器初始化")
    
    try:
        # 测试正常初始化
        scheduler = SimpleDRLScheduler(3, 5)
        print("  ✅ 正常参数初始化成功")
        
        # 验证基本属性
        assert scheduler.machines_count == 3, "机器数量不正确"
        assert scheduler.max_tasks == 5, "最大任务数量不正确"
        assert scheduler.state_dim == 3*2 + 5*3, "状态维度计算错误"
        assert scheduler.action_dim == 3*5, "动作维度计算错误"
        print("  ✅ 基本属性验证通过")
        
        # 验证神经网络
        assert hasattr(scheduler, 'actor'), "Actor网络缺失"
        assert hasattr(scheduler, 'critic'), "Critic网络缺失"
        print("  ✅ 神经网络创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 初始化测试失败: {e}")
        return False

def test_parameter_validation():
    """测试参数验证"""
    print("\n🧪 测试2: 参数验证")
    
    # 测试无效参数
    invalid_params = [
        (0, 5, "机器数量为0"),
        (-1, 5, "机器数量为负数"),
        (3, 0, "任务数量为0"),
        (3, -1, "任务数量为负数"),
    ]
    
    for machines, tasks, description in invalid_params:
        try:
            scheduler = SimpleDRLScheduler(machines, tasks)
            print(f"  ❌ {description} - 应该抛出异常但没有")
            return False
        except ValueError:
            print(f"  ✅ {description} - 正确抛出ValueError")
        except Exception as e:
            print(f"  ❌ {description} - 抛出异常类型错误: {type(e).__name__}")
            return False
    
    print("  ✅ 所有参数验证测试通过")
    return True

def test_state_construction():
    """测试状态构建"""
    print("\n🧪 测试3: 状态构建")
    
    try:
        scheduler = SimpleDRLScheduler(2, 3)
        
        # 创建测试机器
        machines = [
            Machine(0, 100, 100),
            Machine(1, 100, 100)
        ]
        machines[0].cpu_usage = 50
        machines[0].memory_usage = 30
        machines[1].cpu_usage = 20
        machines[1].memory_usage = 80
        
        # 创建测试任务
        tasks = [
            Task(0, 0, 25, 40, 3600),
            Task(1, 5, 15, 20, 1800)
        ]
        
        # 构建状态
        state = scheduler.get_state(machines, tasks)
        
        # 验证状态维度
        expected_dim = 2*2 + 3*3  # 2台机器×2个特征 + 3个任务×3个特征
        assert len(state) == expected_dim, f"状态维度错误: 期望{expected_dim}, 实际{len(state)}"
        
        # 验证状态值
        assert state[0] == 0.5, f"机器0 CPU使用率错误: {state[0]}"
        assert state[1] == 0.3, f"机器0 内存使用率错误: {state[1]}"
        assert state[2] == 0.2, f"机器1 CPU使用率错误: {state[2]}"
        assert state[3] == 0.8, f"机器1 内存使用率错误: {state[3]}"
        
        print("  ✅ 状态构建测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 状态构建测试失败: {e}")
        return False

def test_task_and_machine_classes():
    """测试Task和Machine类"""
    print("\n🧪 测试4: Task和Machine类")
    
    try:
        # 测试Task类
        task = Task(1, 100, 30, 50, 7200)
        assert task.task_id == 1, "任务ID错误"
        assert task.cpu_demand == 30, "CPU需求错误"
        assert task.memory_demand == 50, "内存需求错误"
        assert task.estimated_duration == 7200, "估计时长错误"
        print("  ✅ Task类测试通过")
        
        # 测试Machine类
        machine = Machine(0, 100, 100)
        assert machine.machine_id == 0, "机器ID错误"
        assert machine.cpu_capacity == 100, "CPU容量错误"
        assert machine.memory_capacity == 100, "内存容量错误"
        assert machine.cpu_usage == 0, "初始CPU使用率错误"
        assert machine.memory_usage == 0, "初始内存使用率错误"
        print("  ✅ Machine类测试通过")
        
        # 测试任务分配
        assert machine.can_accommodate(task), "应该能够容纳任务"
        assert machine.assign_task(task, 0), "任务分配应该成功"
        assert machine.cpu_usage == 30, "CPU使用率更新错误"
        assert machine.memory_usage == 50, "内存使用率更新错误"
        assert len(machine.running_tasks) == 1, "运行任务列表更新错误"
        print("  ✅ 任务分配测试通过")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Task和Machine类测试失败: {e}")
        return False

def test_simulator():
    """测试模拟器"""
    print("\n🧪 测试5: 模拟器功能")
    
    try:
        # 创建小规模模拟器
        sim = SimpleSimulator(2, 3)
        
        # 验证初始化
        assert len(sim.machines) == 2, "机器数量错误"
        assert len(sim.waiting_tasks) == 3, "任务数量错误"
        print("  ✅ 模拟器初始化成功")
        
        # 测试FCFS算法
        fcfs_metrics = sim.run_fcfs()
        assert 'avg_weighted_turnaround' in fcfs_metrics, "FCFS指标缺失"
        assert 'makespan' in fcfs_metrics, "FCFS完工时间缺失"
        print("  ✅ FCFS算法运行成功")
        
        # 测试DRL算法（减少轮数以加快测试）
        drl_metrics = sim.run_drl(episodes=2)
        assert 'avg_weighted_turnaround' in drl_metrics, "DRL指标缺失"
        assert 'makespan' in drl_metrics, "DRL完工时间缺失"
        print("  ✅ DRL算法运行成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 模拟器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始深度强化学习任务调度器测试")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        test_scheduler_initialization,
        test_parameter_validation,
        test_state_construction,
        test_task_and_machine_classes,
        test_simulator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统功能正常")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，需要检查")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 