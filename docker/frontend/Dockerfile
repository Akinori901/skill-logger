FROM node:22-slim

WORKDIR /app

# 依存を先にインストール（キャッシュ活用）
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

# Vite 開発サーバー（--host でコンテナ外公開）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
