docker desktop start
docker start manus-postgres
docker start manus-redis
uvicorn app.main:app --port 8000