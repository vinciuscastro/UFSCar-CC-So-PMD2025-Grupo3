# Processamento Massivo de Dados: Projeto Prático

- **Tema**: Catálogo Musical
- **Integrantes**:
    - Caike Vinicius dos Santos, 802629, caikesantos@estudante.ufscar.br
    - Ryan Guerra Sakurai, 802639, ryansakurai@estudante.ufscar.br
    - Vinicius Silva Castro, 802138, vscastro59@estudante.ufscar.br

## Resumo

O projeto consiste em uma API web de catálogo musical com funcionalidades de rede social e recomendações personalizadas. Permite consultar informações detalhadas sobre artistas e seus lançamentos (álbuns e EPs), incluindo avaliações feitas pelo usuário. Na gestão de usuários, o sistema oferece cadastro e consulta de perfis, manutenção de lista de amigos e possibilidade de seguir artistas de interesse. Usuários podem avaliar lançamentos musicais e revisar seu histórico de avaliações.

O sistema gera recomendações inteligentes: sugere novos artistas com base nas preferências do usuário, recomenda lançamentos considerando avaliações positivas de amigos e indica potenciais novas amizades por afinidade musical. Assim, a plataforma combina acesso a conteúdo musical, interação social e descobertas personalizadas em uma única experiência.

Como fonte dos dados, será utilizada a API do Spotify, que fornece informações atualizadas sobre artistas, lançamentos e faixas. O projeto utilizará MongoDB para armazenar dados de usuários, artistas e lançamentos, enquanto o Neo4j será empregado para modelar as relações entre esses elementos, permitindo consultas eficientes e recomendações personalizadas.

## Funcionalidades do Sistema

### Catálogo Musical

- Obter dados de um artista
- Obter dados de um lançamento
- Calcular média de avaliações de um lançamento
- Listar avaliações de um lançamento

### Gestão de Usuários e Interações

- Registrar usuário
- Obter dados do usuário
- Listar amigos do usuário
- Listar artistas seguidos pelo usuário
- Avaliar um lançamento
- Listar avaliações de um usuário

### Sistema de Recomendações

- Recomendar artistas por gênero musical
- Recomendar lançamentos por avaliações de amigos
- Recomendar amizades por afinidade de gênero
- Recomendar amizades por similaridade de avaliações

## Ferramentas Escolhidas

### MongoDB

A escolha do MongoDB, um banco de dados orientado a documentos, justifica-se pela natureza semi estruturada dos dados musicais. Artistas, lançamentos e usuários possuem atributos variáveis que se adaptam naturalmente ao modelo de documentos flexíveis. Essa característica permite armazenar entidades com hierarquias aninhadas, como um lançamento contendo uma quantidade variável de faixas, sem exigir esquemas rígidos, facilitando futuras evoluções do modelo de dados. A escalabilidade horizontal do MongoDB também é crucial para lidar com o crescimento esperado do catálogo e base de usuários.

### Neo4j



### Python



### Spotify Web API



## Modelagem dos Dados

### MongoDB

Onde serão armazenados os dados dos usuários, artistas e lançamentos, contendo as seguintes coleções:

- **Usuário:** username (único), nome (opcional), senha, quantidade de amigos, quantidade de artistas seguidos, quantidade de avaliações feitas.
- **Artista:** ID, nome, gêneros, quantidade de seguidores, nível de popularidade, lista de lançamentos.
- **Lançamento:** ID, nome, data de lançamento, quantidade de avaliações, lista de faixas (nome e duração).

### Neo4j

**Tipos de Nó:**

- Artista
- Lançamento
- Gênero
- Usuário

**Tipos de Relacionamento:**

- (Artista) -[Possui]→ (Lançamento)
- (Artista) -[Pertence a]→ (Gênero)
- (Usuário) -[Segue]→ (Artista)
- (Usuário) -[Avaliou {Nota}]→ (Lançamento)
- (Usuário) ←[É Amigo de]→ (Usuário)

## Fluxograma da aplicação
<img src="https://github.com/user-attachments/assets/546bc130-c806-4ea0-a9e8-2c6ee39848bb" width="400"/>
