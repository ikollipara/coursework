uv run flask --app coursework.web:bootstrap_app run --port 8000 --cert cert.pem --key key.pem & \
    npx @tailwindcss/cli -i src/coursework/web/static_src/input.css -o src/coursework/web/static/output.css --watch
