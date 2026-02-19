import os
import importlib
from fastapi import FastAPI
from typing import List


def register_routers(app: FastAPI, api_dir: str = "api") -> List[str]:
    registered_routers = []

    # api 디렉토리의 모든 파일을 스캔
    for filename in os.listdir(api_dir):
        if filename.endswith("_api.py"):
            module_name = filename[:-3]
            module_path = f"{api_dir}.{module_name}"

            try:
                module = importlib.import_module(module_path)

                # router 속성이 있는지 확인
                if hasattr(module, "router"):
                    router = getattr(module, "router")
                    tag = module_name.replace("_api", "").title()

                    # 라우터 등록
                    app.include_router(router, prefix="/api", tags=[tag])
                    registered_routers.append(module_name)
                    print(f"라우터 등록됨: {module_name}")

            except Exception as e:
                print(f"라우터 등록 실패: {module_name}, 에러: {e}")

    return registered_routers


def get_router_info(api_dir: str = "api") -> List[dict]:
    router_info = []

    for filename in os.listdir(api_dir):
        if filename.endswith("_api.py"):
            module_name = filename[:-3]
            module_path = f"{api_dir}.{module_name}"

            try:
                module = importlib.import_module(module_path)

                if hasattr(module, "router"):
                    router_info.append(
                        {
                            "module_name": module_name,
                            "module_path": module_path,
                            "has_router": True,
                        }
                    )
                else:
                    router_info.append(
                        {
                            "module_name": module_name,
                            "module_path": module_path,
                            "has_router": False,
                        }
                    )

            except Exception as e:
                router_info.append(
                    {
                        "module_name": module_name,
                        "module_path": module_path,
                        "has_router": False,
                        "error": str(e),
                    }
                )

    return router_info
