docker stop sandbox-dev

docker rm sandbox-dev

docker build -t sandbox-dev .

docker run -d -p 8080:8080 -p 5900:5900 -p 5901:5901 -p 9222:9222 --name sandbox-dev sandbox-dev
