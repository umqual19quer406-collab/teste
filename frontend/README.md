# Frontend - Mini Protheus

Aplicacao React + Vite + TypeScript.

## Requisitos

- Node.js 20+

## Configuracao

Arquivo `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Se preferir, copie a base a partir de `frontend/.env.example`.

O app valida essa variavel no startup. Se ela estiver ausente ou vazia, a inicializacao falha com erro explicito.

Para deploy na Vercel, configure `VITE_API_BASE_URL` com a URL publica do backend, por exemplo:

```env
VITE_API_BASE_URL=https://mini-protheus-api.onrender.com
```

## Comandos

Instalar dependencias:

```powershell
npm install
```

Desenvolvimento:

```powershell
npm run dev
```

Lint:

```powershell
npm run lint
```

Build de producao:

```powershell
npm run build
```

Preview local do build:

```powershell
npm run preview
```
