import json
import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any

class CheckinRecorder:
    """签到记录管理器 - 负责记录所有签到活动"""
    
    def __init__(self, record_file: str = "checkin_records.json"):
        """
        初始化签到记录管理器
        
        Args:
            record_file: 记录文件路径，默认为当前目录下的 checkin_records.json
        """
        self.record_file = record_file
        self.lock = threading.Lock()  # 用于确保线程安全的锁
        self._initialize_file()
    
    def _initialize_file(self) -> None:
        """初始化记录文件，如果文件不存在则创建"""
        try:
            if not os.path.exists(self.record_file):
                # 创建初始的空记录文件
                initial_data = {
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0",
                        "total_records": 0
                    },
                    "records": []
                }
                with open(self.record_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                print(f"[记录器] 创建新的签到记录文件: {self.record_file}")
            else:
                print(f"[记录器] 使用现有的签到记录文件: {self.record_file}")
        except Exception as e:
            print(f"[记录器] 初始化文件失败: {str(e)}")
            raise
    
    def _load_data(self) -> Dict[str, Any]:
        """加载记录文件数据"""
        try:
            with open(self.record_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[记录器] 加载数据失败: {str(e)}")
            # 如果文件损坏，备份并重新创建
            self._backup_corrupted_file()
            self._initialize_file()
            return self._load_data()
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """原子性保存数据到文件"""
        try:
            # 使用临时文件确保写入的原子性
            temp_file = self.record_file + '.tmp'
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性地将临时文件重命名为正式文件
            os.replace(temp_file, self.record_file)
            return True
        except Exception as e:
            print(f"[记录器] 保存数据失败: {str(e)}")
            # 清理临时文件
            temp_file = self.record_file + '.tmp'
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    
    def _backup_corrupted_file(self) -> None:
        """备份损坏的文件"""
        try:
            if os.path.exists(self.record_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.record_file}.backup_{timestamp}"
                os.rename(self.record_file, backup_file)
                print(f"[记录器] 已备份损坏文件到: {backup_file}")
        except Exception as e:
            print(f"[记录器] 备份文件失败: {str(e)}")
    
    def add_record(self, 
                   course_name: str, 
                   course_id: Optional[str], 
                   rollcall_id: str, 
                   checkin_code: Optional[str],
                   checkin_type: str,
                   latitude: Optional[float] = None,
                   longitude: Optional[float] = None,
                   success: bool = True,
                   distance: Optional[float] = None,
                   additional_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加签到记录
        
        Args:
            course_name: 课程名称
            course_id: 课程ID（可选）
            rollcall_id: 签到活动ID
            checkin_code: 签到码（数字签到时提供）
            checkin_type: 签到类型（"数字签到" 或 "雷达签到"）
            latitude: 纬度（雷达签到时提供）
            longitude: 经度（雷达签到时提供）
            success: 签到是否成功
            distance: 距离数据（雷达签到时提供）
            additional_info: 额外信息（可选）
            
        Returns:
            bool: 记录是否成功添加
        """
        with self.lock:  # 确保线程安全
            try:
                # 构建记录数据
                record = {
                    "timestamp": datetime.now().isoformat(),
                    "course_info": {
                        "name": course_name,
                        "id": course_id
                    },
                    "rollcall_info": {
                        "id": rollcall_id,
                        "type": checkin_type
                    },
                    "checkin_result": {
                        "success": success,
                        "code": checkin_code,
                        "coordinates": {
                            "latitude": latitude,
                            "longitude": longitude
                        } if latitude is not None and longitude is not None else None,
                        "distance": distance
                    },
                    "additional_info": additional_info or {}
                }
                
                # 加载现有数据
                data = self._load_data()
                
                # 添加新记录
                data["records"].append(record)
                
                # 更新元数据
                data["metadata"]["total_records"] = len(data["records"])
                data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                # 保存数据
                if self._save_data(data):
                    print(f"[记录器] 签到记录已保存: {course_name} - {checkin_type} - {'成功' if success else '失败'}")
                    return True
                else:
                    print("[记录器] 保存签到记录失败")
                    return False
                    
            except Exception as e:
                print(f"[记录器] 添加记录时发生错误: {str(e)}")
                return False
    
    def get_records(self, 
                   course_name: Optional[str] = None, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   success_only: bool = False) -> list:
        """
        获取签到记录
        
        Args:
            course_name: 按课程名称过滤（可选）
            start_date: 开始日期 (YYYY-MM-DD格式，可选)
            end_date: 结束日期 (YYYY-MM-DD格式，可选)
            success_only: 是否只返回成功的记录（可选）
            
        Returns:
            list: 过滤后的记录列表
        """
        try:
            data = self._load_data()
            records = data["records"]
            
            # 应用过滤器
            if course_name:
                records = [r for r in records if r["course_info"]["name"] == course_name]
            
            if start_date:
                records = [r for r in records if r["timestamp"] >= start_date]
            
            if end_date:
                records = [r for r in records if r["timestamp"] <= end_date + "T23:59:59"]
            
            if success_only:
                records = [r for r in records if r["checkin_result"]["success"]]
            
            return records
            
        except Exception as e:
            print(f"[记录器] 获取记录失败: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取签到统计信息"""
        try:
            data = self._load_data()
            records = data["records"]
            
            if not records:
                return {
                    "total_records": 0,
                    "successful_checkins": 0,
                    "failed_checkins": 0,
                    "success_rate": 0.0,
                    "courses": {},
                    "checkin_types": {},
                    "last_checkin": None
                }
            
            # 基本统计
            total_records = len(records)
            successful_checkins = len([r for r in records if r["checkin_result"]["success"]])
            failed_checkins = total_records - successful_checkins
            success_rate = (successful_checkins / total_records) * 100 if total_records > 0 else 0
            
            # 课程统计
            courses = {}
            for record in records:
                course_name = record["course_info"]["name"]
                if course_name not in courses:
                    courses[course_name] = {"total": 0, "successful": 0}
                courses[course_name]["total"] += 1
                if record["checkin_result"]["success"]:
                    courses[course_name]["successful"] += 1
            
            # 签到类型统计
            checkin_types = {}
            for record in records:
                checkin_type = record["rollcall_info"]["type"]
                if checkin_type not in checkin_types:
                    checkin_types[checkin_type] = {"total": 0, "successful": 0}
                checkin_types[checkin_type]["total"] += 1
                if record["checkin_result"]["success"]:
                    checkin_types[checkin_type]["successful"] += 1
            
            # 最近签到
            last_checkin = records[-1]["timestamp"] if records else None
            
            return {
                "total_records": total_records,
                "successful_checkins": successful_checkins,
                "failed_checkins": failed_checkins,
                "success_rate": round(success_rate, 2),
                "courses": courses,
                "checkin_types": checkin_types,
                "last_checkin": last_checkin
            }
            
        except Exception as e:
            print(f"[记录器] 获取统计信息失败: {str(e)}")
            return {}
    
    def export_records(self, export_file: Optional[str] = None) -> bool:
        """
        导出记录到指定文件
        
        Args:
            export_file: 导出文件路径，如果为None则使用时间戳命名
            
        Returns:
            bool: 导出是否成功
        """
        try:
            if export_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_file = f"checkin_records_export_{timestamp}.json"
            
            data = self._load_data()
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[记录器] 记录已导出到: {export_file}")
            return True
            
        except Exception as e:
            print(f"[记录器] 导出记录失败: {str(e)}")
            return False
    
    def clear_old_records(self, days_to_keep: int = 30) -> int:
        """
        清理旧的记录
        
        Args:
            days_to_keep: 保留最近多少天的记录
            
        Returns:
            int: 删除的记录数量
        """
        with self.lock:
            try:
                data = self._load_data()
                records = data["records"]
                
                if not records:
                    return 0
                
                # 计算截止时间
                cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
                
                # 过滤出新记录
                new_records = []
                removed_count = 0
                
                for record in records:
                    record_time = datetime.fromisoformat(record["timestamp"]).timestamp()
                    if record_time >= cutoff_time:
                        new_records.append(record)
                    else:
                        removed_count += 1
                
                if removed_count > 0:
                    # 更新数据并保存
                    data["records"] = new_records
                    data["metadata"]["total_records"] = len(new_records)
                    data["metadata"]["last_updated"] = datetime.now().isoformat()
                    data["metadata"]["cleaned_at"] = datetime.now().isoformat()
                    data["metadata"]["removed_records"] = removed_count
                    
                    if self._save_data(data):
                        print(f"[记录器] 已清理 {removed_count} 条旧记录，保留最近 {days_to_keep} 天的数据")
                        return removed_count
                    else:
                        print("[记录器] 清理记录失败")
                        return 0
                else:
                    print(f"[记录器] 没有需要清理的旧记录")
                    return 0
                    
            except Exception as e:
                print(f"[记录器] 清理记录时发生错误: {str(e)}")
                return 0