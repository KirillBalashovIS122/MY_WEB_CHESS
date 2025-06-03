FROM node:18

WORKDIR /app/frontend
COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]