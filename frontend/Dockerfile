FROM node:18-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev"]
