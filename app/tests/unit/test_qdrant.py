import asyncio
import os
import sys

# Ensure app/ directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.config import settings
from services.qdrant_service import qdrant_service


async def main() -> None:
    print("=" * 60)
    print("🔍 Testing Qdrant Connection & Payload Index Initialization")
    print("=" * 60)
    print(f"📌 QDRANT_URL: '{settings.QDRANT_URL}'")
    print(
        f"📌 QDRANT_API_KEY: {'[CONFIGURED]' if settings.QDRANT_API_KEY else '[EMPTY / IN-MEMORY FALLBACK]'}"
    )
    print(f"📌 COLLECTION_NAME: '{settings.QDRANT_COLLECTION_NAME}'")
    print("-" * 60)

    try:
        print("⏳ Running ensure_collection_and_index()...")
        await qdrant_service.ensure_collection_and_index(vector_size=1024)
        print("✅ SUCCESS: Connected to Qdrant!")
        print(
            f"✅ Collection '{settings.QDRANT_COLLECTION_NAME}' and keyword payload indexes ('tenant_id', 'file_name') are verified."
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to verify Qdrant connection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
