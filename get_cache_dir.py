import matplotlib
import shutil

cache_dir = matplotlib.get_cachedir()
print(f"Matplotlib 캐시 디렉토리: {cache_dir}")

# 아래 주석을 해제하고 스크립트를 다시 실행하면 캐시를 직접 삭제할 수도 있습니다.
# 다만, 삭제는 매우 신중하게 진행해야 하며, 삭제 후에는 반드시 애플리케이션을 재시작해야 합니다.
# try:
#     shutil.rmtree(cache_dir)
#     print(f"성공적으로 Matplotlib 캐시 디렉토리를 삭제했습니다: {cache_dir}")
#     print("애플리케이션(Uvicorn 서버)을 완전히 종료 후 재시작해주세요.")
# except Exception as e:
#     print(f"캐시 디렉토리 삭제 중 오류 발생: {e}") 