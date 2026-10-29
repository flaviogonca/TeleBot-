# Telegram Connect

Aplicação web desenvolvida em Python para interagir com um bot do Telegram através de uma interface gráfica acessível pelo navegador.

O projeto permite automatizar o envio e a receção de mensagens, visualizar imagens, interagir com botões e menus do bot e gerir a sessão de uma conta Telegram sem ter de utilizar diretamente a aplicação Telegram para cada interação.

> **Nota:** Este projeto utiliza uma sessão de utilizador Telegram através de uma biblioteca como Telethon. Não é um bot criado através do BotFather. A conta utilizada para iniciar sessão tem de pertencer ao utilizador e a interação deve respeitar os termos de utilização do Telegram e as regras do bot de destino.

---

## Funcionalidades

- **Interface web responsiva:** design adaptado a computadores, tablets e telemóveis.
- **Autenticação pela interface web:** introdução do número de telefone, código de confirmação e palavra-passe de verificação em duas etapas, quando solicitada.
- **Chat privado:** comunicação com o bot configurado.
- **Envio de mensagens:** envio de texto através do navegador.
- **Receção de mensagens:** atualização periódica da conversa.
- **Suporte para imagens:** envio e visualização de imagens, conforme suportado pelo backend.
- **Botões e menus interativos:** possibilidade de selecionar opções disponibilizadas pelo bot.
- **Gestão da sessão:** botão para terminar a sessão e duração máxima configurável de 25 minutos.
- **Backend Python:** processamento das operações Telegram no servidor.
- **Preparação para deploy:** estrutura que pode ser adaptada para alojamento num servidor web.

## Tecnologias

| Tecnologia | Utilização |
|---|---|
| Python 3.10+ | Backend |
| Flask | Servidor web e API |
| Telethon | Comunicação com o Telegram através de uma conta de utilizador |
| HTML5 | Estrutura da interface |
| CSS3 | Estilos e design responsivo |
| JavaScript | Comunicação com a API e atualização do chat |
| python-dotenv | Gestão de variáveis de ambiente |

A versão concreta das dependências deve ser definida no ficheiro `requirements.txt`.

---

## Estrutura do projeto

Uma estrutura possível para o projeto é:

```text
TeleBot/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── templates/
    └── index.html
```

**Descrição dos ficheiros e diretórios:**

- `app.py`: ponto de entrada da aplicação, caso seja utilizado como servidor principal. Módulo de integração Telegram ou servidor Flask, conforme a organização atual do projeto.
- `requirements.txt`: dependências Python.
- `.env`: credenciais e configurações privadas.
- `.env.example`: exemplo das variáveis necessárias, sem credenciais reais.
- `templates/index.html`: interface gráfica.
- `static/`: ficheiros estáticos, se forem utilizados.
- `sessions/`: sessões locais do Telethon, se a aplicação as guardar neste diretório.
- `instance/`: configurações ou dados locais da aplicação, se aplicável.

> Os nomes `app.py` e `web_telegram.py` são exemplos de organização. Ajusta os comandos de execução ao ficheiro que efetivamente inicia o servidor Flask.

---

## Requisitos

Antes de começar, confirma que tens instalado:

- Python 3.10 ou superior.
- pip.
- Uma conta Telegram válida.
- Credenciais de API do Telegram (`API_ID` e `API_HASH`).
- Acesso ao bot que pretendes utilizar, neste projeto `@Dlaylama_bot`.

As credenciais de API podem ser obtidas através do portal oficial do Telegram:

https://my.telegram.org/

A conta deve conseguir iniciar uma conversa com o bot de destino. O projeto não necessita de um token de bot do BotFather quando utiliza uma sessão de utilizador através do Telethon.

---

## 1. Clonar ou abrir o projeto

Se o projeto já estiver no teu computador, entra diretamente na respetiva pasta:

```bash
cd ~/TeleBot
```

Se estiver alojado num repositório Git, utiliza o endereço desse repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd TeleBot
```

Substitui `<URL_DO_REPOSITORIO>` pelo endereço real do teu repositório.

## 2. Criar um ambiente virtual

No Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Atualiza o pip:

```bash
python -m pip install --upgrade pip
```

## 3. Instalar as dependências

Instala as dependências declaradas no projeto:

```bash
pip install -r requirements.txt
```

Se ainda não existir um `requirements.txt`, cria um com as dependências realmente utilizadas pelo backend. Por exemplo:

```text
Flask
Telethon
python-dotenv
```

Depois instala-as:

```bash
pip install -r requirements.txt
```

Para um deploy estável, fixa as versões das dependências após validar o funcionamento da aplicação.

---

## 4. Configurar as variáveis de ambiente

Cria um ficheiro `.env` na raiz do projeto:

```dotenv
FLASK_SECRET_KEY=SUBSTITUIR_POR_UMA_CHAVE_ALEATORIA
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=SUBSTITUIR_PELO_API_HASH_REAL
TELEGRAM_BOT_USERNAME=Dlaylama_bot
SESSION_NAME=minha_conta_telegram
SESSION_TIMEOUT_MINUTES=25
```

### O que significa cada variável?

| Variável | Descrição |
|---|---|
| `FLASK_SECRET_KEY` | Chave secreta para proteger as sessões Flask |
| `TELEGRAM_API_ID` | Identificador da aplicação Telegram |
| `TELEGRAM_API_HASH` | Chave de API da aplicação Telegram |
| `TELEGRAM_BOT_USERNAME` | Nome de utilizador do bot de destino |
| `SESSION_NAME` | Nome ou caminho-base da sessão Telethon |
| `SESSION_TIMEOUT_MINUTES` | Duração pretendida da sessão autenticada |

Os nomes acima são uma proposta de configuração. O código Python tem de ler estas mesmas variáveis para que tenham efeito.

**Importante:** não coloques o teu número de telefone, código de confirmação, palavra-passe 2FA, `API_HASH` ou ficheiros de sessão num repositório público.

Gera uma chave secreta para o Flask, por exemplo:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia o resultado para `FLASK_SECRET_KEY`.

---

## 5. Configurar o bot de destino

Neste projeto, o bot de destino é:

```text
@Dlaylama_bot
```

O nome de utilizador identifica o bot com o qual pretendes conversar. Não é necessário conhecer o token privado do bot de outra pessoa para interagir com ele através de uma conta Telegram autorizada.

O fluxo esperado é:

1. Abrir a aplicação web.
2. Introduzir a palavra-passe de acesso ao painel, se estiver configurada.
3. Introduzir o número de telefone da conta Telegram.
4. Solicitar o código de confirmação.
5. Introduzir o código recebido através dos canais oficiais do Telegram.
6. Introduzir a palavra-passe 2FA, se for solicitada.
7. Abrir a conversa com o bot.
8. Enviar mensagens e interagir com os menus disponibilizados.

A autenticação deve ser implementada no backend com tratamento adequado de erros e dos desafios de autenticação adicionais.

---

## 6. Executar a aplicação

Ativa o ambiente virtual e inicia o ficheiro que contém a aplicação Flask.

Se o ponto de entrada for `app.py`:

```bash
python app.py
```

Se o ponto de entrada for `web_telegram.py`:

```bash
python web_telegram.py
```

Utiliza apenas o comando correspondente à organização efetiva do teu projeto.

Quando o servidor iniciar, abre no navegador:

http://127.0.0.1:5000

Para parar o servidor local, utiliza `Ctrl+C` no terminal em que está a correr.

---

## 7. Funcionamento da interface

### Autenticação

A aplicação apresenta os campos de autenticação necessários. Os pedidos são enviados ao backend através da API HTTP.

### Conversa

A interface apresenta as mensagens recebidas e enviadas. O JavaScript consulta periodicamente o endpoint de mensagens para atualizar a conversa.

### Botões e menus

Quando o bot disponibiliza botões inline, o backend deve identificar a mensagem e a opção selecionada e executar a ação correspondente através do Telethon.

Nem todos os botões são equivalentes: alguns abrem URLs, enquanto outros enviam callbacks ao Telegram.

### Imagens

O backend deve tratar o envio de imagens e disponibilizar as imagens recebidas à interface através de um mecanismo de acesso seguro.

### Terminar sessão

O botão de terminar sessão deve chamar o endpoint de logout e invalidar a sessão da aplicação.

O limite de 25 minutos deve ser validado no servidor. Um contador no navegador, por si só, não garante que uma sessão expire realmente.

---

## 8. Endpoints esperados

A interface apresentada no `templates/index.html` utiliza endpoints semelhantes aos seguintes:

| Método | Endpoint | Finalidade |
|---|---|---|
| `GET` | `/` | Apresentar a interface web |
| `POST` | `/api/access` | Autenticar no painel web |
| `GET` | `/api/state` | Consultar o estado e o tempo restante da sessão |
| `POST` | `/api/telegram/phone` | Solicitar código de autenticação |
| `POST` | `/api/telegram/code` | Validar o código recebido |
| `POST` | `/api/telegram/password` | Validar a palavra-passe 2FA |
| `GET` | `/api/messages` | Obter as mensagens da conversa |
| `POST` | `/api/send` | Enviar uma mensagem de texto |
| `POST` | `/api/upload` | Enviar uma imagem |
| `POST` | `/api/click` | Interagir com um botão inline |
| `POST` | `/api/logout` | Terminar a sessão |

Estes endpoints representam o contrato esperado pela interface. A sua existência e o respetivo comportamento dependem da implementação no backend.

As respostas JSON devem utilizar um formato consistente, por exemplo:

```json
{
  "ok": true,
  "status": "authenticated"
}
```

Em caso de erro:

```json
{
  "ok": false,
  "error": "Não foi possível concluir a operação."
}
```

---

## 9. Segurança

Como a aplicação utiliza uma conta Telegram real, a proteção da autenticação é essencial.

### Recomendações obrigatórias

- Não guardar códigos de confirmação nem palavras-passe 2FA em logs.
- Não expor `API_HASH`, chaves secretas ou ficheiros `.session`.
- Utilizar HTTPS em ambientes públicos.
- Ativar proteção CSRF nas operações que alteram o estado.
- Validar e limitar o tamanho das mensagens e dos ficheiros enviados.
- Validar as permissões e o estado da sessão em todos os endpoints protegidos.
- Aplicar um limite de tentativas de autenticação.
- Não expor a aplicação diretamente à Internet enquanto estiver configurada apenas para desenvolvimento.
- Proteger as imagens e os ficheiros recebidos contra acessos não autorizados.
- Não desativar a verificação TLS.
- Não partilhar a sessão autenticada com outros utilizadores.

### Ficheiro `.gitignore`

Cria um `.gitignore` com regras como:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
*.session
*.session-journal
sessions/
instance/
.pytest_cache/
.coverage
```

Se já tiveres ficheiros de sessão ou credenciais no Git, adicioná-los ao `.gitignore` não remove os ficheiros do histórico. É necessário removê-los do repositório e, se houver exposição de segredos, proceder à sua rotação ou revogação.

---

## 10. Preparação para deploy

O servidor de desenvolvimento Flask é adequado para testes locais, mas não deve ser utilizado como servidor de produção.

Para um deploy público, prepara os seguintes elementos:

- Servidor WSGI de produção, como Gunicorn, se o ambiente for compatível.
- HTTPS com certificado válido.
- Variáveis de ambiente configuradas no serviço de alojamento.
- Armazenamento persistente e protegido para a sessão Telethon.
- Processo de inicialização e encerramento controlados.
- Registos sem credenciais ou conteúdo privado.
- Limites de pedidos, proteção CSRF e autenticação do painel.
- Política de cópias de segurança e recuperação da sessão.
- Testes de expiração e invalidação da sessão no servidor.

Exemplo de instalação do Gunicorn:

```bash
pip install gunicorn
```

Se o objeto Flask se chamar `app` e estiver definido em `app.py`, um comando possível é:

```bash
gunicorn --workers 1 --bind 127.0.0.1:8000 app:app
```

Este comando é apenas um exemplo. O módulo e o nome do objeto Flask devem corresponder ao código real.

A utilização de um único worker pode simplificar o acesso à sessão Telethon, mas não substitui a gestão adequada do ciclo de vida do cliente nem o controlo de concorrência. Para produção, a integração Telegram deve ter um ciclo de vida bem definido e evitar múltiplos processos a utilizar simultaneamente a mesma sessão.

**Antes de publicar a aplicação**, confirma que o logout, a expiração ao fim de 25 minutos, a proteção dos endpoints e o armazenamento da sessão são efetivamente implementados no servidor.

---

## 11. Resolução de problemas

### Erro: `The phone number is invalid`

Verifica se o número está no formato internacional, incluindo o indicativo do país.

Exemplo ilustrativo:

```text
+244923456789
```

Utiliza o teu número real, não o exemplo.

### Erro: código de confirmação inválido

- Confirma se introduziste o código mais recente.
- Verifica se o código expirou.
- Evita solicitar códigos repetidamente.
- Confirma se o backend está a utilizar o pedido de autenticação correto.

### Erro: palavra-passe 2FA necessária

Se a conta tiver a verificação em duas etapas ativada, a autenticação tem de tratar esse passo adicional.

### Erro: sessão já utilizada

Não abras simultaneamente vários processos que utilizem o mesmo ficheiro de sessão Telethon. Fecha processos antigos e verifica o estado da sessão antes de reiniciar a aplicação.

### Erro `404` em `/favicon.ico`

O navegador está a solicitar um ícone que ainda não existe. É um erro normalmente inofensivo. Podes adicionar um favicon em `static/` e referenciá-lo no HTML.

### A interface não recebe mensagens

Verifica:

- Se o cliente Telethon está ligado.
- Se o endpoint `/api/messages` funciona.
- Se a conta iniciou a conversa com o bot.
- Se os erros do backend estão a ser registados sem dados sensíveis.
- Se o formato JSON devolvido corresponde ao esperado pelo JavaScript.

---

## 12. Utilização responsável

A aplicação destina-se à automatização pessoal de uma conversa autorizada.

Para reduzir problemas com a conta Telegram:

- Utiliza apenas uma sessão que controlas.
- Não automatizes mensagens em massa nem contactos não solicitados.
- Não contornes mecanismos de segurança ou limites impostos pelo Telegram.
- Evita pedidos repetitivos e desnecessários.
- Respeita as regras e os limites definidos pelo bot de destino.
- Não utilizes a aplicação para contornar restrições ou executar ações proibidas.

A utilização do Telethon não garante que uma conta esteja isenta de restrições. O risco depende do comportamento da automação e das regras aplicáveis.

---

## 13. Estado do projeto

Este README documenta a estrutura e o funcionamento pretendidos para o Telegram Connect. A existência efetiva de cada funcionalidade depende do código instalado.

Antes de considerar o projeto pronto para produção, valida:

- [ ] Autenticação web completa.
- [ ] Envio e receção de mensagens.
- [ ] Envio e visualização de imagens.
- [ ] Funcionamento dos botões inline.
- [ ] Logout funcional.
- [ ] Expiração de sessão validada no servidor após 25 minutos.
- [ ] Proteção CSRF e autenticação nos endpoints.
- [ ] Segredos e sessões excluídos do Git.
- [ ] Execução com servidor de produção.
- [ ] Testes de segurança e recuperação de erros.

---

## Licença

Define uma licença antes de distribuir o projeto. Se for para uso exclusivamente pessoal, podes mantê-lo privado e documentar as condições de utilização no próprio repositório.