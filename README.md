# Processamento Massivo de Dados: Projeto Prático

- **Tema**: Catálogo Musical
- **Integrantes**:
    - Caike Vinicius dos Santos, 802629, caikesantos@estudante.ufscar.br
    - Ryan Guerra Sakurai, 802639, ryansakurai@estudante.ufscar.br
    - Vinicius Silva Castro, 802138, vscastro59@estudante.ufscar.br

## Resumo

O projeto consiste em uma API web de catálogo musical com funcionalidades de rede social e recomendações personalizadas. Permite consultar informações detalhadas sobre artistas e seus lançamentos (álbuns e EPs), incluindo avaliações feitas pelo usuário. Na gestão de usuários, o sistema oferece cadastro e consulta de perfis, manutenção de lista de amigos e possibilidade de seguir artistas de interesse. Usuários podem avaliar lançamentos musicais e revisar seu histórico de avaliações.

O sistema gera recomendações inteligentes: sugere novos artistas com base nas preferências do usuário, recomenda lançamentos considerando avaliações positivas de amigos e indica potenciais novas amizades por afinidade musical. Assim, a plataforma combina acesso a conteúdo musical, interação social e descobertas personalizadas em uma única experiência.

## Funcionalidades do Sistema

### Catálogo Musical

- Obter dados de um artista:
    - ID
    - Nome
    - Gêneros
    - Bio (opcional)
    - Quantidade de seguidores
    - Média de avaliações
    - *Preview* da lista de lançamentos (ID, nome e ano de lançamento)
- Listar músicas de um artista
- Obter dados de um lançamento:
    - ID
    - Nome
    - Data de lançamento
    - Média de avaliações
    - Lista de faixas (índice, nome e duração)
- Listar avaliações de um lançamento

### Gestão de Usuários

- Registrar usuário
- Obter dados do usuário:
    - *Username*
    - Nome (opcional)
    - Bio (opcional)
    - Quantidade de amigos
    - Quantidade de artistas seguidos
    - Quantidade de avaliações feitas
- Listar amigos do usuário
- Listar artistas seguidos pelo usuário
- Listar avaliações feitas pelo usuário

### Interações

- Adicionar um amigo
- Seguir um artista
- Avaliar um lançamento

### Sistema de Recomendações

- Recomendar artistas por gênero musical
- Recomendar lançamentos por avaliações de amigos
- Recomendar amizades por afinidade de gênero
- Recomendar amizades por similaridade de avaliações

## Ferramentas Escolhidas

### MongoDB

A escolha do MongoDB como banco de dados orientado a documentos justifica-se pela natureza semiestruturada dos dados musicais e de usuários, que apresentam atributos variáveis e opcionais. Essa flexibilidade permite acomodar campos como biografias de artistas ou usuários que podem estar ausentes em alguns registros, bem como gerenciar estruturas de tamanho variável como a lista de lançamentos de um artista, que cresce indefinidamente. Além disso, a organização em documentos concentra todos os dados relacionados a uma entidade em um único local, otimizando operações como a recuperação de todas as músicas de um artista. Essa abordagem evita percursos custosos e desnecessários em um grafo do Neo4j, por exemplo, para essa operação básica. Complementando essas características, a escalabilidade horizontal nativa do MongoDB também é essencial para o crescimento projetado do catálogo musical e da base de usuários.

### Neo4j

O Neo4j, um banco de dados orientado a grafos, foi selecionado para gerenciar as relações complexas inerentes às funcionalidades sociais e de recomendações. A natureza conectada dos dados, como usuários seguindo artistas, formando amizades e avaliando lançamentos, é naturalmente representada através de nós e arestas. Essa modelagem permite consultas eficientes de caminhos complexos, essenciais para recomendações como "encontrar usuários que avaliaram positivamente os mesmos lançamentos" ou "descobrir artistas similares através de gêneros compartilhados".

### Python

Para o desenvolvimento da API, optou-se por Python com o framework Flask. Python foi escolhido pelo vasto ecossistema de bibliotecas, facilidade de desenvolvimento e natureza dinâmica. O Flask oferece leveza e flexibilidade para construir endpoints RESTful de forma simples e eficiente. Além disso, serão usados as bibliotecas PyMongo e Neo4j Python Driver para comunicação com os bancos de dados.

## Fontes dos Dados

Os dados musicais (artistas, lançamentos e faixas) serão extraídas da [Spotify Web API](https://developer.spotify.com/documentation/web-api) através da biblioteca [Spotipy](https://spotipy.readthedocs.io/en/2.25.1/), assegurando informações atualizadas e precisas sobre o catálogo musical. Para os dados de usuários, utilizaremos uma abordagem mista: a biblioteca Faker, do Python, será responsável pela geração de dados mais básicos como nomes, enquanto a [Gemini Developer API](https://ai.google.dev/gemini-api/docs) complementará com elementos criativos como biografias personalizadas. Quanto às conexões sociais e às interações serão estabelecidas manualmente através de *scripts* Python.

```mermaid
flowchart TB
    A[Cliente] -->|Requisição por API| B[Servidor Flask]
    B -->|Resposta| A

    B -->|Modifica| C[MongoDB]
    C -->|Retorna dados| B
    
    B -->|Modifica| D[Neo4j]
    D -->|Retorna dados| B

    E[Spotify API] -->|Fornece dados| F[Script Python]
    G[Gemini API] -->|Fornece dados| F

    F[Script Python] -->|Insere dados| C
    F[Script Python] -->|Insere dados| D
```

## Modelagem dos Dados

### MongoDB

Onde serão armazenados os dados dos usuários, artistas e lançamentos, contendo as seguintes coleções:

- **Usuário**: *username* (único), nome (opcional), senha, bio (opcional), lista de amigos, lista de artistas seguidos, lista de avaliações feitas.
    - **Avaliação**: ID do lançamento, artista, nome do lançamento, nota.
- **Artista**: ID, nome, gêneros, bio (opcional), quantidade de seguidores, lista de lançamentos.
    - **Lançamento**: ID (possui índice), nome, data de lançamento, quantidade de avaliações, lista de faixas, lista de avaliações.
        - **Faixa**: índice, nome, duração.
        - **Avaliação**: *username*, nota.

### Neo4j

**Tipos de Nó:**

- Artista {ID, nível de popularidade}
- Lançamento {ID}
- Gênero {Nome}
- Usuário {Username}

**Tipos de Relacionamento:**

- (Artista) -[Lança]→ (Lançamento)
- (Artista) -[Pertence a]→ (Gênero)
- (Usuário) -[Segue]→ (Artista)
- (Usuário) -[Avaliou {Nota}]→ (Lançamento)
- (Usuário) ←[É Amigo de]→ (Usuário)

### Desenvolvimento
Inicialmente, foi definida a modelagem dos dados no MongoDB e no Neo4j, de forma a atender aos requisitos de catálogo musical e de interação social. Em seguida, foram implementados scripts em Python que utilizam a biblioteca Spotipy para recuperar informações de artistas, álbuns e faixas diretamente da Spotify Web API. A geração automatizada de perfis de usuário e biografias foi realizada por meio das ferramentas Faker e Gemini Developer API.
A API foi desenvolvida em Flask diretamente nas rotas, concentrando as operações de acesso aos bancos de dados e a lógica de negócio. As requisições são processadas nessas rotas, com o uso do PyMongo para manipulação dos documentos no MongoDB e do driver oficial do Neo4j para interações com os nós e relacionamentos no grafo. Também foram criados scripts adicionais em Python para popular o grafo com relacionamentos aleatórios entre usuários, artistas e avaliações, simulando uma rede social funcional e fornecendo dados para o sistema de recomendações.
O sistema de recomendações foi projetado para combinar afinidade de gêneros musicais e conexões sociais. Por meio de consultas em Cypher, foi possível identificar artistas que compartilham gêneros com os já seguidos ou avaliados positivamente, além de recomendar lançamentos apreciados por contatos próximos na rede. Um método híbrido também foi adotado, priorizando lançamentos com alta média entre os amigos e, ao mesmo tempo, sugerindo artistas com perfis similares aos gostos do usuário. As recomendações são geradas em tempo real, refletindo imediatamente novas avaliações e relações sociais.

### Dificuldades encontradas
Durante a geração de biografias dos usuários, a principal limitação técnica enfrentada foi a cota diária da Gemini Developer API. Como o número de chamadas era restrito, a criação dos perfis precisou ser distribuída ao longo de vários dias, o que impactou o ritmo de populamento do sistema. Também foi necessário realizar diversos ajustes nos prompts enviados à API para obter descrições que fossem criativas e ao mesmo tempo coerentes com o contexto musical.
A criação dos scripts para popular os relacionamentos no Neo4j também apresentou dificuldades. Foi preciso desenvolver uma lógica capaz de gerar conexões aleatórias entre usuários, artistas e avaliações de forma realista e equilibrada, garantindo que o grafo representasse uma rede social funcional. Esse processo exigiu várias iterações para ajustar a densidade das conexões e evitar um grafo artificialmente raso ou excessivamente denso. Além disso, a conexão com o Aura se mostrava instável, frequentemente sendo interrompida durante a execução dos scripts, o que atrapalhava a continuidade do populamento. A população em massa no Neo4j também se mostrou consideravelmente mais lenta em comparação com o MongoDB, aumentando o tempo necessário para completar a inserção de dados.
Também houve bastante dificuldade na criação do script de geração automática de relacionamentos no Neo4j. A conexão com o Aura se mostrava instável e frequentemente era interrompida durante a execução, o que atrapalhava o progresso do populamento. Além disso, a população em massa no Neo4j demonstrou ser consideravelmente mais lenta do que no MongoDB, o que tornou o processo de inserção de grandes volumes de dados mais trabalhoso. Somando a isso, consultas muito profundas ou que envolviam um grande volume de nós acabavam comprometendo ainda mais a performance geral do banco. Para contornar esses problemas, foram realizadas otimizações nas consultas Cypher, aplicando limites adequados e ajustando os índices, garantindo um funcionamento mais fluido nas interações com o grafo.


### Conclusão
O desenvolvimento resultou em uma API que integra catálogo musical, rede social e recomendações inteligentes de maneira coesa e eficiente. A aplicação permite acesso a informações atualizadas da Spotify Web API, gerenciamento de amizades, seguimento de artistas e registro de avaliações, alimentando um grafo de relacionamentos que serve de base para sugestões personalizadas.
A solução demonstra que é possível combinar bancos de dados documentais e de grafos em um mesmo sistema, atendendo a diferentes tipos de consulta com eficiência. A utilização do Flask de forma direta simplifica a arquitetura e oferece uma base sólida e flexível, pronta para receber expansões como interfaces gráficas ou autenticação externa.

---

## Primeiros Passos

1. **Clone o repositório**  
   ```bash
   git clone https://github.com/vinciuscastro/UFSCar-CC-So-PMD2025-Grupo3.git
   cd UFSCar-CC-So-PMD2025-Grupo3
    ```

2. **Crie o arquivo `.env` na raiz do projeto**
   Preencha com suas credenciais:

   ```env
   MONGODB_USERNAME=
   MONGODB_PASSWORD=
   NEO4J_USERNAME=
   NEO4J_PASSWORD=
   ```

3. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie a aplicação**

   ```bash
   python src/app/main.py
   ```

5. **Acesse no navegador**
   A API estará disponível em:

   ```
   http://127.0.0.1:5000
   ```

---

## Documentação da API

### 🎤 Artistas
#### `GET /v1/artists/<artist_id>`
**Descrição**  
Retorna as informações de um artista (nome, gêneros, bio, seguidores, média de avaliações e prévia de lançamentos).

**Parâmetros de rota**  
- `artist_id` (string): ID do artista no MongoDB.

**Resposta 200 OK**  
```json
{
  "id": "abc123",
  "name": "Arctic Monkeys",
  "genres": ["rock","indie"],
  "bio": "Banda inglesa formada em Sheffield...",
  "qt_followers": 824,
  "average_rating": 4.2,
  "releases": [
    {
      "id": "rel001",
      "name": "AM",
      "release_year": 2013
    }
  ]
}
````

**Erros possíveis**

* `404 Not Found`: artista não encontrado.

---

#### `GET /v1/artists/<artist_id>/tracks`

**Descrição**
Retorna todas as faixas de um artista, agrupadas por nome da faixa e listando em quais lançamentos ela aparece, ordenadas alfabeticamente.

**Parâmetros de rota**

* `artist_id` (string): ID do artista.

**Resposta 200 OK**

```json
{
  "artist": {
    "id": "abc123",
    "name": "Arctic Monkeys"
  },
  "items": [
    {
      "name": "Do I Wanna Know?",
      "releases": [
        {
          "id": "rel001",
          "name": "AM"
        }
      ]
    }
  ]
}
```



**Erros possíveis**

* `404 Not Found`: artista não encontrado.

---

### 💿 Lançamentos (Releases)

#### `GET /v1/releases/<release_id>`

**Descrição**
Retorna detalhes de um lançamento (nome, data, artista, lista de faixas e média de avaliações).

**Parâmetros de rota**

* `release_id` (string): ID do lançamento.

**Resposta 200 OK**

```json
{
  "id": "rel001",
  "name": "AM",
  "artist": {
    "id": "abc123",
    "name": "Arctic Monkeys"
  },
  "release_date": "2013-09-09",
  "rating_average": 4.4,
  "tracks": [
    {
      "index": 1,
      "name": "Do I Wanna Know?",
      "duration": 272
    }
  ]
}
```

**Erros possíveis**

* `404 Not Found`: lançamento não encontrado.

---

#### `GET /v1/releases/<release_id>/ratings`

**Descrição**
Retorna todas as avaliações de usuários para um lançamento.

**Parâmetros de rota**

* `release_id` (string): ID do lançamento.

**Resposta 200 OK**

```json
{
  "release": {
    "id": "rel001",
    "name": "AM",
    "artist": "Arctic Monkeys"
  },
  "items": [
    {
      "username": "user123",
      "rating": 4.5
    }
  ]
}
```

**Erros possíveis**

* `404 Not Found`: lançamento não encontrado.

---

### 🧑‍🤝‍🧑 Usuários (Users)

#### `GET /v1/users/<username>`

**Descrição**
Retorna dados do usuário (username, nome, bio, quantidade de amigos, avaliações e follows).

**Parâmetros de rota**

* `username` (string)

**Resposta 200 OK**

```json
{
  "username": "johndoe",
  "name": "John Doe",
  "bio": "Apaixonado por música...",
  "qt_friends": 5,
  "qt_ratings": 10,
  "qt_follows": 3
}
```

**Erros possíveis**

* `404 Not Found`: usuário não encontrado.

---

#### `GET /v1/users/<username>/friends`

**Descrição**
Lista todos os amigos de um usuário.

**Parâmetros de rota**

* `username` (string)

**Resposta 200 OK**

```json
{
  "username": "johndoe",
  "items": ["alice","bob","charlie"]
}
```

**Erros possíveis**

* `404 Not Found`: usuário não encontrado.

---

#### `GET /v1/users/<username>/ratings`

**Descrição**
Lista todas as avaliações feitas por um usuário.

**Parâmetros de rota**

* `username` (string)

**Resposta 200 OK**

```json
{
  "username": "johndoe",
  "items": [
    {"id":"rel001","artist":"Arctic Monkeys","name":"AM","rating":4.5},
    ...
  ]
}
```

**Erros possíveis**

* `404 Not Found`: usuário não encontrado.

---

#### `GET /v1/users/<username>/follows`

**Descrição**
Lista todos os artistas seguidos por um usuário.

**Parâmetros de rota**

* `username` (string)

**Resposta 200 OK**

```json
{
  "username": "johndoe",
  "items": [
    {"id":"art123","name":"Arctic Monkeys"},
    ...
  ]
}
```

**Erros possíveis**

* `404 Not Found`: usuário não encontrado.

---

#### `POST /v1/users`

**Descrição**
Registra um novo usuário.

**Body (JSON)**

```json
{
  "username": "johndoe",
  "password": "senha123",
  "name": "John Doe",       // opcional
  "bio": "Ama rock clássico" // opcional
}
```

**Resposta 201 Created**

* Sem conteúdo no body.

**Erros possíveis**

* `400 Bad Request`: campo obrigatório faltando.
* `409 Conflict`: usuário já existe.

---


#### `DELETE /v1/users/<username>`
**Descrição**  
Remove completamente um usuário, suas amizades, avaliações e follows, tanto em MongoDB quanto em Neo4j.

**Parâmetros de rota**  
- `username` (string): nome de usuário a ser deletado.

**Resposta 200 OK**  
- Sem conteúdo no body.

**Erros possíveis**  
- `404 Not Found`: usuário não encontrado.

---

#### `PATCH /v1/users/<username>`
**Descrição**  
Atualiza senha, nome ou bio de um usuário. Campos não informados permanecem inalterados; valores vazios removem o campo.

**Parâmetros de rota**  
- `username` (string): nome de usuário a ser atualizado.

**Body (JSON)**  
```json
{
  "password": "novasenha",  // opcional
  "name": "Novo Nome",      // opcional (string vazia para remover)
  "bio": "Nova bio"         // opcional (string vazia para remover)
}
````

**Resposta 200 OK**

* Sem conteúdo no body.

**Erros possíveis**

* `404 Not Found`: usuário não encontrado.
* `400 Bad Request`: nenhum campo válido fornecido.

---

#### `POST /v1/users/<username>/ratings`

**Descrição**
Adiciona uma avaliação a um lançamento para o usuário, atualizando MongoDB e Neo4j.

**Parâmetros de rota**

* `username` (string): nome de usuário que avalia.

**Body (JSON)**

```json
{
  "id": "rel001",     // ID do release
  "rating": 4.5       // nota (número)
}
```


**Resposta 201 Created**

* Sem conteúdo no body.

**Erros possíveis**

* `400 Bad Request`: campo obrigatório faltando (`id` ou `rating`).
* `404 Not Found`: usuário ou release não encontrados.
* `409 Conflict`: avaliação já existe para este usuário e release.

---

#### `DELETE /v1/users/<username>/ratings/<release_id>`

**Descrição**
Remove a avaliação de um lançamento feito pelo usuário, tanto em MongoDB quanto em Neo4j.

**Parâmetros de rota**

* `username` (string)
* `release_id` (string)

**Resposta 200 OK**

* Sem conteúdo no body.

**Erros possíveis**

* `404 Not Found`: usuário, release ou avaliação não encontrados.

---

#### `POST /v1/users/<username>/follows`

**Descrição**
Faz o usuário seguir um artista. Incrementa contador de seguidores e cria relacionamento em Neo4j.

**Parâmetros de rota**

* `username` (string)

**Body (JSON)**

```json
{
  "id": "art123"   // ID do artista
}
```

**Resposta 201 Created**

* Sem conteúdo no body.

**Erros possíveis**

* `400 Bad Request`: campo `id` faltando.
* `404 Not Found`: usuário ou artista não encontrados.
* `409 Conflict`: já existe follow para este usuário e artista.

---

#### `DELETE /v1/users/<username>/follows/<artist_id>`

**Descrição**
Faz o usuário deixar de seguir um artista. Decrementa contador de seguidores e remove relacionamento em Neo4j.

**Parâmetros de rota**

* `username` (string)
* `artist_id` (string)

**Resposta 200 OK**

* Sem conteúdo no body.

**Erros possíveis**

* `404 Not Found`: usuário, artista ou relacionamento follow não encontrados.

---

#### `POST /v1/users/<username>/friends`

**Descrição**
Adiciona outro usuário como amigo (bidirecional) em MongoDB e cria relacionamento em Neo4j.

**Parâmetros de rota**

* `username` (string)

**Body (JSON)**

```json
{
  "username": "friendUser"   // nome de usuário do amigo
}
```

**Resposta 201 Created**

* Sem conteúdo no body.

**Erros possíveis**

* `400 Bad Request`: campo `username` faltando.
* `404 Not Found`: usuário ou amigo não encontrados.
* `409 Conflict`: amizade já existe.

---

#### `DELETE /v1/users/<username>/friends/<friend_username>`

**Descrição**
Remove a amizade entre dois usuários, tanto em MongoDB quanto em Neo4j.

**Parâmetros de rota**

* `username` (string)
* `friend_username` (string)

**Resposta 200 OK**

* Sem conteúdo no body.

**Erros possíveis**

* `404 Not Found`: usuário, amigo ou relacionamento de amizade não encontrados.

---

### 🔁 Recomendações (Recs)

> **Em desenvolvimento** 

```md

```

