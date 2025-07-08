# Stage 1: Build the application
FROM node:16-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install

# Stage 2: Create the final, smaller image
FROM node:16-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 8080
CMD ["npm", "start"]