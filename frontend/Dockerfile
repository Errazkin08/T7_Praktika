FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package*.json ./

# Install dependencies with clean npm install
RUN npm ci || npm install

# Then copy the rest of the application
COPY . .

# Add these environment variables for better development experience
ENV NODE_ENV=development
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

EXPOSE 80

CMD ["npm", "run", "dev"]