"""
Cosmos DB 초기화 스크립트
- top_movers 컬렉션 생성
"""
from azure.cosmos import exceptions
from src.core.database import get_database

def init_top_movers_container():
    """top_movers 컨테이너 생성"""
    try:
        database = get_database()
        
        # 컨테이너가 이미 존재하는지 확인
        try:
            container = database.get_container_client("top_movers")
            properties = container.read()
            print(f"✅ 'top_movers' 컨테이너가 이미 존재합니다.")
            print(f"   - Partition key: {properties['partitionKey']}")
            return
        except exceptions.CosmosResourceNotFoundError:
            pass
        
        # 컨테이너 생성
        print("📦 'top_movers' 컨테이너를 생성합니다...")
        container = database.create_container(
            id="top_movers",
            partition_key={"paths": ["/id"], "kind": "Hash"}
        )
        print("✅ 'top_movers' 컨테이너가 성공적으로 생성되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

def main():
    print("=" * 60)
    print("Cosmos DB 초기화 시작")
    print("=" * 60)
    
    init_top_movers_container()
    
    print("=" * 60)
    print("초기화 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
