# DLP Monitor — Sistema de Detecção de Risco de Vazamento de Dados

Software de monitoramento (DLP — *Data Loss Prevention*) que observa sinais de
possível vazamento de dados no computador do usuário (câmera, teclado,
área de transferência, processos, dispositivos USB), calcula um **grau de
risco** e alerta o administrador com evidências (screenshot + foto da
webcam) no momento do evento.

## ⚠️ Aviso legal (LGPD)

Este software captura tela, webcam e área de transferência — dados
potencialmente sensíveis, inclusive de terceiros que apareçam na câmera.
**Antes de usar em produção:**

- Informe formalmente os usuários monitorados (política de uso aceitável,
  termo assinado, aviso visível).
- Defina base legal, finalidade específica e prazo de retenção das
  evidências coletadas, conforme a LGPD (Lei 13.709/2018).
- Restrinja o acesso às evidências apenas a pessoas autorizadas


## Arquitetura

```
dlp_monitor/
├── main.py                  # orquestra todos os monitores (rode como um programa)
├── admin_panel.py           # PAINEL DO ADMINISTRADOR — programa desktop separado
├── config.py                # limiares, palavras-chave, e-mail, senha do painel, etc.
├── risk_engine.py           # agrega eventos e calcula o grau de risco
├── evidence.py               # captura screenshot + foto da webcam
├── alert_manager.py         # envia alerta por e-mail / webhook / grava no banco local
├── alert_store.py           # banco SQLite local compartilhado (sem rede)
├── screen_ocr.py             # OCR da tela p/ checar CPF/telefone/endereço/nome visíveis
├── monitors/
│   ├── camera_monitor.py    # rostos extras / ausência suspeita na webcam
│   ├── clipboard_monitor.py # dados sensíveis copiados (CPF, cartão, etc.)
│   ├── keyboard_monitor.py  # PrintScreen / Win+Shift+S
│   ├── usb_monitor.py       # pendrives/HDs externos conectados
│   └── process_monitor.py   # apps de gravação de tela / acesso remoto
├── alertas.db                # banco SQLite (gerado em runtime)
└── evidencias/               # screenshots e fotos capturados (gerado em runtime)
```

## Como funciona o grau de risco

Cada monitor registra **eventos** no `RiskEngine` com um peso (ex.: um
PrintScreen vale 3 pontos, um recorte com CPF vale 4, dois rostos na
câmera valem 4). Os eventos são somados numa janela deslizante de tempo
(`JANELA_AGREGACAO_SEGUNDOS`, padrão 30s) e classificados:

| Score na janela | Nível    |
|------------------|----------|
| < 3               | BAIXO (não alerta) |
| 3 – 5             | MÉDIO    |
| 6 – 8             | ALTO     |
| ≥ 9               | CRÍTICO  |

Ao ultrapassar o nível BAIXO, o sistema captura um screenshot + foto da
webcam e envia o alerta ao administrador (e-mail e/ou webhook).

## Instalação

```bash
cd dlp_monitor
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Windows**: o `keyboard` e o hook global de teclado normalmente exigem
> executar o script como Administrador.
> **macOS**: conceda permissão de Acessibilidade e Câmera ao Terminal/Python
> em Preferências do Sistema → Segurança e Privacidade.
> **Linux**: pode ser necessário rodar com `sudo` para o hook de teclado, e
> instalar `python3-tk`/`scrot` para o `pyautogui` funcionar.

## Configuração

Defina as variáveis de ambiente (ou edite `config.py` diretamente):

```bash
export DLP_SMTP_HOST="smtp.suaempresa.com"
export DLP_SMTP_PORT=587
export DLP_SMTP_USER="alertas@suaempresa.com"
export DLP_SMTP_PASSWORD="sua_senha_ou_app_password"
export DLP_ADMIN_EMAIL="seguranca@suaempresa.com"
# opcional: export DLP_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

Ajuste também em `config.py`:
- `KEYWORDS_SENSIVEIS` / `REGEX_SENSIVEIS`: o que conta como dado sensível.
- `PROCESSOS_RISCO`: quais aplicativos são considerados de risco.
- `PESOS_EVENTO` e os `LIMIAR_*`: sensibilidade do sistema de risco.

## Executando

```bash
python main.py
```

O sistema roda em segundo plano, monitorando continuamente. Os logs vão
para `dlp_monitor.log` e as evidências para a pasta `evidencias/`.

## Scanner de foto de dado sensível (câmera + OCR)

Esta é a funcionalidade principal do projeto: detectar quando alguém tira
foto da tela com o celular **enquanto ela mostra dado pessoal** (CPF,
telefone, endereço, ou campos como "nome completo"/"RG").

**Como funciona:**

1. A cada ~1s, a webcam captura um frame e um modelo de detecção de objetos
   (YOLOv8, treinado no dataset COCO) verifica se há um **celular** na cena.
2. Se um celular for detectado, o sistema tira um **screenshot da tela
   naquele instante** e roda **OCR** (leitura de texto na imagem) para
   checar se há CPF, telefone, CEP, ou rótulos como "nome:"/"endereço"
   visíveis.
3. Só quando as duas coisas coincidem — **celular + tela sensível** — é
   que o evento `CAMERA_FOTO_DADOS_SENSIVEIS` é registrado, com peso
   suficiente para ir direto ao nível **CRÍTICO** e alertar o
   administrador com as evidências.
4. Se o celular for detectado mas a tela não tiver dado sensível
   confirmado, ainda assim registra um evento de menor gravidade
   (`CAMERA_OBJETO_SUSPEITO`) — não ignora, mas também não dispara pânico.

Isso evita alarme falso de alguém apenas segurando o celular perto do
computador sem estar fotografando dado nenhum.

### Instalação extra necessária

Essa funcionalidade depende de duas coisas além do `pip install -r requirements.txt`:

**1. Tesseract-OCR** (motor de OCR — é um programa do sistema, não só uma
biblioteca Python):

- **Windows**: baixe o instalador em
  https://github.com/UB-Mannheim/tesseract/wiki e instale normalmente.
  Durante a instalação, marque o pacote de idioma **Portuguese**.
  Depois, configure o caminho (ajuste se instalou em outro lugar):

  ```bash
  set DLP_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```

- **Linux**: `sudo apt install tesseract-ocr tesseract-ocr-por`
- **macOS**: `brew install tesseract tesseract-lang`

**2. Modelo YOLOv8** — baixado automaticamente na primeira execução do
`main.py` (precisa de internet nesse primeiro momento; depois fica salvo
localmente em cache). Se preferir desativar a detecção de celular
completamente (por exemplo, num computador sem internet ou mais fraco):

```bash
set DLP_DETECCAO_CELULAR=0
```

Nesse caso o monitor de câmera continua funcionando normalmente para
detecção de rosto (mais de uma pessoa / ausência prolongada), só a
detecção de celular fica desligada.

## Painel do administrador (programa separado, sem rede)

O painel roda como um **programa desktop independente** (Tkinter), não um
site — ele não abre nenhuma porta de rede nem servidor HTTP. Ele apenas lê
o mesmo arquivo SQLite local (`alertas.db`) onde o monitor grava os
alertas, então os dois programas conversam só através desse arquivo em
disco.

Rode em duas janelas de terminal separadas:

```bash
# Terminal 1 — o monitor, rodando em segundo plano
python main.py

# Terminal 2 — o painel do administrador
python admin_panel.py
```

O painel mostra a lista de alertas (mais recentes primeiro), coloridos por
grau de risco, e ao clicar em um deles exibe os eventos que o geraram e as
evidências capturadas (screenshot + foto da webcam, quando disponíveis). A
lista é atualizada automaticamente a cada poucos segundos.

Para exigir uma senha simples ao abrir o painel (proteção contra uso
casual por quem sentar na máquina — **não** é autenticação de rede):

```bash
export DLP_PAINEL_SENHA="uma_senha_qualquer"
python admin_panel.py
```

## Limitações e próximos passos

- A detecção de celular usa o modelo genérico YOLOv8n (rápido, mas não
  especializado). Para mais precisão em ambientes de produção, considere
  treinar/usar um modelo mais robusto (ex.: yolov8s.pt/yolov8m.pt) ou uma
  câmera com melhor ângulo/iluminação da tela.
- O monitor de USB usa uma heurística simples (`part.opts` no
  Windows / `/media` no Linux); em ambientes reais, vale usar APIs
  nativas do SO (ex.: `WMI` no Windows) para maior precisão.
- Para ambientes com múltiplos colaboradores, considere centralizar os
  alertas em um dashboard/SIEM em vez de (ou além de) e-mail.
