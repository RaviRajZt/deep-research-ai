# ============================================
# Deep Research Platform - Frontend Dockerfile (Production)
# ============================================
# Multi-stage build using Next.js standalone output mode.
# Produces a minimal image with no node_modules in the final layer.
# ============================================

# ---------- Stage 1: Dependencies ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# ---------- Stage 2: Builder ----------
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Build-time env args (injected from docker-compose.prod.yml)
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_ENV

RUN npm run build

# ---------- Stage 3: Runner ----------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Next.js standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER nextjs

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
