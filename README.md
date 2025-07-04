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
