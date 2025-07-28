# 🤝 Contribuindo para o Bot de Trading Binance

Obrigado pelo interesse em contribuir! Este guia vai te ajudar a começar.

## 🚀 Como Contribuir

### 1. Fork e Clone

```bash
# Fork o repositório no GitHub
# Clone seu fork
git clone https://github.com/seu-usuario/binance-trading-bot.git
cd binance-trading-bot

# Adicione o repositório original como upstream
git remote add upstream https://github.com/original-user/binance-trading-bot.git
```

### 2. Configuração do Ambiente

```bash
# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências de desenvolvimento
pip install -e ".[dev]"

# Configure pre-commit hooks (opcional)
pre-commit install
```

### 3. Padrões de Desenvolvimento

#### Estilo de Código
- **Python**: Seguimos PEP 8
- **Formatação**: Black com linha de 88 caracteres
- **Linting**: Flake8
- **Type Hints**: Obrigatório para funções públicas

#### Estrutura de Commits
```
tipo(escopo): descrição breve

Descrição mais detalhada se necessário.

- Mudança específica 1
- Mudança específica 2

Resolves #123
```

**Tipos válidos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação/estilo
- `refactor`: Refatoração de código
- `test`: Testes
- `chore`: Tarefas de manutenção

### 4. Processo de Desenvolvimento

#### Criando uma Feature

```bash
# Crie uma branch para sua feature
git checkout -b feat/nova-funcionalidade

# Desenvolva e teste
python -m pytest tests/
python demo_bot.py

# Commit suas mudanças
git add .
git commit -m "feat(strategy): adiciona indicador Bollinger Bands"

# Push para seu fork
git push origin feat/nova-funcionalidade
```

#### Testes

```bash
# Execute todos os testes
python -m pytest tests/ -v

# Testes com cobertura
python -m pytest tests/ --cov=. --cov-report=html

# Teste apenas um módulo
python -m pytest tests/test_strategy.py -v
```

#### Qualidade do Código

```bash
# Formatação automática
black .

# Verificação de estilo
flake8 .

# Type checking
mypy .
```

## 📝 Diretrizes Específicas

### Adicionando Novos Indicadores

1. **Arquivo**: `indicators.py`
2. **Testes**: `tests/test_indicators.py`
3. **Documentação**: Docstring detalhada

```python
def new_indicator(self, data: Dict, period: int = 20) -> np.ndarray:
    """
    Calcula novo indicador técnico.
    
    Args:
        data: Dados OHLCV
        period: Período do indicador
        
    Returns:
        Array com valores do indicador
        
    Raises:
        ValueError: Se dados insuficientes
    """
    # Implementação aqui
    pass
```

### Modificando Estratégias

1. **Arquivo**: `strategy.py`
2. **Configuração**: `config.yaml.example`
3. **Testes**: Cenários de compra/venda/espera

### Gestão de Risco

1. **Arquivo**: `risk_manager.py`
2. **Validação**: Sempre validar parâmetros
3. **Logs**: Registrar decisões importantes

## 🧪 Tipos de Contribuição

### 🐛 Reportando Bugs

Use o template de issue:

```markdown
**Descrição do Bug**
Descrição clara do problema.

**Para Reproduzir**
1. Configuração usada
2. Passos para reproduzir
3. Comportamento esperado vs atual

**Ambiente**
- OS: [Windows/Linux/Mac]
- Python: [versão]
- Dependências: [versões relevantes]

**Logs**
```
[Cole logs relevantes aqui]
```
```

### ✨ Sugerindo Features

```markdown
**Funcionalidade Desejada**
Descrição da funcionalidade.

**Motivação**
Por que seria útil?

**Solução Proposta**
Como poderia ser implementada?

**Alternativas Consideradas**
Outras abordagens possíveis.
```

### 📚 Melhorando Documentação

- README.md
- Docstrings
- Comentários de código
- Exemplos de uso
- Tutoriais

## 🔒 Segurança

### Diretrizes de Segurança

1. **Nunca** commite chaves de API
2. **Sempre** use `.env` para secrets
3. **Valide** entradas do usuário
4. **Sanitize** logs (sem dados sensíveis)

### Reportando Vulnerabilidades

Envie email para: security@tradingbot.com

**Não** abra issues públicas para vulnerabilidades.

## 📋 Checklist para Pull Requests

- [ ] Código formatado com Black
- [ ] Testes passando (`pytest tests/`)
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Type hints adicionados
- [ ] Logs apropriados
- [ ] Configuração de exemplo atualizada
- [ ] Sem hardcoded secrets

## 🏆 Reconhecimento

Contribuidores são reconhecidos:

1. **README.md**: Seção de contribuidores
2. **CHANGELOG.md**: Créditos por versão
3. **GitHub**: Contributors page

## 📞 Suporte

- **Issues**: Bugs e features
- **Discussions**: Perguntas gerais
- **Discord**: Chat em tempo real
- **Email**: dev@tradingbot.com

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a MIT License.

---

**Obrigado por contribuir! 🚀**