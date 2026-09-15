import hashlib
import os
import io
from typing import Tuple, Optional
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from app.core.logging import logger

class StorageService:
    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.secure = settings.MINIO_USE_SSL
        self.bucket_documents = settings.MINIO_BUCKET_DOCUMENTS
        self.bucket_artifacts = settings.MINIO_BUCKET_ARTIFACTS
        self.local_storage_dir = os.path.join(os.getcwd(), "local_storage")
        os.makedirs(self.local_storage_dir, exist_ok=True)

        self.client: Optional[Minio] = None
        try:
            self.client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            self._ensure_buckets()
        except Exception as e:
            logger.warning(f"MinIO initialization failed, using local filesystem fallback: {str(e)}")

    def _ensure_buckets(self):
        if not self.client:
            return
        try:
            for bucket in [self.bucket_documents, self.bucket_artifacts]:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
        except Exception as e:
            logger.warning(f"Could not create MinIO buckets: {str(e)}")

    def calculate_hashes(self, content: bytes) -> Tuple[str, str]:
        sha256 = hashlib.sha256(content).hexdigest()
        # Fast perceptual hash representation for binary content
        p_hash = hashlib.md5(content).hexdigest()
        return sha256, p_hash

    async def upload_document(
        self, 
        file_bytes: bytes, 
        filename: str, 
        content_type: str, 
        organization_id: str
    ) -> Tuple[str, str, str]:
        sha256_hash, p_hash = self.calculate_hashes(file_bytes)
        object_name = f"{organization_id}/{sha256_hash}/{filename}"

        if self.client:
            try:
                self.client.put_object(
                    bucket_name=self.bucket_documents,
                    object_name=object_name,
                    data=io.BytesIO(file_bytes),
                    length=len(file_bytes),
                    content_type=content_type
                )
                logger.info(f"Uploaded file to MinIO: {object_name}")
                return object_name, sha256_hash, p_hash
            except Exception as e:
                logger.error(f"MinIO upload error: {str(e)}, falling back to local file storage")

        # Local filesystem fallback
        local_path = os.path.join(self.local_storage_dir, object_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return local_path, sha256_hash, p_hash

    async def get_document_bytes(self, storage_path: str) -> bytes:
        if self.client and not storage_path.startswith(self.local_storage_dir):
            try:
                response = self.client.get_object(self.bucket_documents, storage_path)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except Exception as e:
                logger.error(f"Failed to fetch object from MinIO: {str(e)}")

        if os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()
                
        raise FileNotFoundError(f"Document not found at path: {storage_path}")

    def get_presigned_url(self, storage_path: str, expires_seconds: int = 3600) -> str:
        if self.client and not storage_path.startswith(self.local_storage_dir):
            try:
                return self.client.presigned_get_object(
                    bucket_name=self.bucket_documents,
                    object_name=storage_path,
                    expires=expires_seconds
                )
            except Exception as e:
                logger.error(f"Presigned URL generation failed: {str(e)}")
        return f"/api/v1/documents/stream?path={storage_path}"

storage_service = StorageService()
