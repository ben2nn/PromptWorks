"""
画廊API响应格式验证工具

用于验证所有画廊API接口返回格式的一致性
"""

from typing import Any, Dict, List, Optional
import json
from pydantic import BaseModel, ValidationError


class PaginationModel(BaseModel):
    """分页信息模型"""
    page: Optional[int] = None
    pageSize: Optional[int] = None
    total: Optional[int] = None
    totalPages: Optional[int] = None


class SuccessResponseModel(BaseModel):
    """成功响应模型"""
    success: bool
    data: Optional[Any] = None
    pagination: Optional[PaginationModel] = None


class ErrorDetailModel(BaseModel):
    """错误详情模型"""
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponseModel(BaseModel):
    """错误响应模型"""
    success: bool
    error: ErrorDetailModel


class ResponseValidator:
    """响应格式验证器"""
    
    @staticmethod
    def validate_success_response(response_data: Dict[str, Any]) -> bool:
        """
        验证成功响应格式
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            bool: 验证是否通过
        """
        try:
            SuccessResponseModel(**response_data)
            return True
        except ValidationError as e:
            print(f"成功响应格式验证失败: {e}")
            return False
    
    @staticmethod
    def validate_error_response(response_data: Dict[str, Any]) -> bool:
        """
        验证错误响应格式
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            bool: 验证是否通过
        """
        try:
            ErrorResponseModel(**response_data)
            return True
        except ValidationError as e:
            print(f"错误响应格式验证失败: {e}")
            return False
    
    @staticmethod
    def validate_response(response_data: Dict[str, Any]) -> bool:
        """
        验证响应格式（自动判断成功或错误）
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            bool: 验证是否通过
        """
        if not isinstance(response_data, dict):
            print("响应数据必须是字典格式")
            return False
        
        if "success" not in response_data:
            print("响应数据缺少 'success' 字段")
            return False
        
        if response_data.get("success") is True:
            return ResponseValidator.validate_success_response(response_data)
        else:
            return ResponseValidator.validate_error_response(response_data)
    
    @staticmethod
    def check_required_fields(response_data: Dict[str, Any]) -> List[str]:
        """
        检查响应数据中缺失的必需字段
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            List[str]: 缺失的字段列表
        """
        missing_fields = []
        
        if "success" not in response_data:
            missing_fields.append("success")
            return missing_fields
        
        if response_data.get("success") is True:
            # 成功响应可以没有data字段，但如果有pagination则必须有data
            if "pagination" in response_data and "data" not in response_data:
                missing_fields.append("data (required when pagination is present)")
        else:
            # 错误响应必须有error字段
            if "error" not in response_data:
                missing_fields.append("error")
            else:
                error = response_data["error"]
                if not isinstance(error, dict):
                    missing_fields.append("error (must be object)")
                else:
                    if "code" not in error:
                        missing_fields.append("error.code")
                    if "message" not in error:
                        missing_fields.append("error.message")
        
        return missing_fields
    
    @staticmethod
    def validate_data_types(response_data: Dict[str, Any]) -> List[str]:
        """
        验证响应数据中字段的数据类型
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            List[str]: 类型错误列表
        """
        type_errors = []
        
        # 验证success字段类型
        if "success" in response_data and not isinstance(response_data["success"], bool):
            type_errors.append("success must be boolean")
        
        if response_data.get("success") is True:
            # 验证分页信息类型
            if "pagination" in response_data:
                pagination = response_data["pagination"]
                if not isinstance(pagination, dict):
                    type_errors.append("pagination must be object")
                else:
                    for field in ["page", "pageSize", "total", "totalPages"]:
                        if field in pagination and not isinstance(pagination[field], int):
                            type_errors.append(f"pagination.{field} must be integer")
        else:
            # 验证错误信息类型
            if "error" in response_data:
                error = response_data["error"]
                if isinstance(error, dict):
                    if "code" in error and not isinstance(error["code"], str):
                        type_errors.append("error.code must be string")
                    if "message" in error and not isinstance(error["message"], str):
                        type_errors.append("error.message must be string")
        
        return type_errors


def validate_gallery_response_format(response_data: Any) -> Dict[str, Any]:
    """
    完整验证画廊API响应格式
    
    Args:
        response_data: 响应数据
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "response_type": None
    }
    
    # 基本格式检查
    if not isinstance(response_data, dict):
        result["errors"].append("响应数据必须是JSON对象")
        return result
    
    # 检查必需字段
    missing_fields = ResponseValidator.check_required_fields(response_data)
    if missing_fields:
        result["errors"].extend([f"缺少必需字段: {field}" for field in missing_fields])
    
    # 检查数据类型
    type_errors = ResponseValidator.validate_data_types(response_data)
    if type_errors:
        result["errors"].extend([f"数据类型错误: {error}" for error in type_errors])
    
    # 如果有错误，直接返回
    if result["errors"]:
        return result
    
    # 使用Pydantic模型验证
    is_valid = ResponseValidator.validate_response(response_data)
    result["valid"] = is_valid
    
    # 确定响应类型
    if response_data.get("success") is True:
        result["response_type"] = "success"
        if "data" not in response_data:
            result["warnings"].append("成功响应建议包含data字段")
    else:
        result["response_type"] = "error"
    
    return result


# 测试用例
def test_response_formats():
    """测试各种响应格式"""
    
    test_cases = [
        # 成功响应 - 带数据
        {
            "name": "成功响应 - 带数据",
            "data": {
                "success": True,
                "data": [{"id": 1, "name": "test"}]
            }
        },
        # 成功响应 - 带分页
        {
            "name": "成功响应 - 带分页",
            "data": {
                "success": True,
                "data": [{"id": 1, "name": "test"}],
                "pagination": {
                    "page": 1,
                    "pageSize": 20,
                    "total": 100,
                    "totalPages": 5
                }
            }
        },
        # 错误响应
        {
            "name": "错误响应",
            "data": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "参数验证失败"
                }
            }
        },
        # 错误响应 - 带详情
        {
            "name": "错误响应 - 带详情",
            "data": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "参数验证失败",
                    "details": {"field": "limit", "value": -1}
                }
            }
        },
        # 无效响应 - 缺少success字段
        {
            "name": "无效响应 - 缺少success字段",
            "data": {
                "data": [{"id": 1}]
            }
        },
        # 无效响应 - success类型错误
        {
            "name": "无效响应 - success类型错误",
            "data": {
                "success": "true",
                "data": []
            }
        }
    ]
    
    print("画廊API响应格式验证测试")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n测试用例: {test_case['name']}")
        print(f"输入数据: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
        
        result = validate_gallery_response_format(test_case['data'])
        
        print(f"验证结果: {'✓ 通过' if result['valid'] else '✗ 失败'}")
        print(f"响应类型: {result['response_type']}")
        
        if result['errors']:
            print("错误:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("警告:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        print("-" * 30)


if __name__ == "__main__":
    test_response_formats()