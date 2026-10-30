-- Estrutura SQLite. Execute antes da carga de demonstração.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS setores (
	id INTEGER NOT NULL, 
	nome VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nome)
);

CREATE TABLE IF NOT EXISTS usuarios (
	id INTEGER NOT NULL, 
	nome VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	senha_hash VARCHAR NOT NULL, 
	perfil VARCHAR NOT NULL, 
	ativo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS equipamentos (
	id INTEGER NOT NULL, 
	codigo VARCHAR NOT NULL, 
	nome VARCHAR NOT NULL, 
	modelo VARCHAR NOT NULL, 
	fabricante VARCHAR NOT NULL, 
	localizacao VARCHAR NOT NULL, 
	setor_id INTEGER NOT NULL, 
	criticidade VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	ativo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(setor_id) REFERENCES setores (id)
);

CREATE TABLE IF NOT EXISTS chamados (
	id INTEGER NOT NULL, 
	titulo VARCHAR NOT NULL, 
	descricao TEXT NOT NULL, 
	equipamento_id INTEGER NOT NULL, 
	solicitante_id INTEGER NOT NULL, 
	tecnico_id INTEGER, 
	categoria VARCHAR NOT NULL, 
	prioridade VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	criado_em VARCHAR NOT NULL, 
	resolvido_em VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(equipamento_id) REFERENCES equipamentos (id), 
	FOREIGN KEY(solicitante_id) REFERENCES usuarios (id), 
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS historico (
	id INTEGER NOT NULL, 
	chamado_id INTEGER NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	mensagem VARCHAR NOT NULL, 
	tipo VARCHAR NOT NULL, 
	criado_em VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chamado_id) REFERENCES chamados (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS ordens (
	id INTEGER NOT NULL, 
	chamado_id INTEGER NOT NULL, 
	tecnico_id INTEGER NOT NULL, 
	status VARCHAR NOT NULL, 
	diagnostico VARCHAR NOT NULL, 
	solucao VARCHAR NOT NULL, 
	criado_em VARCHAR NOT NULL, 
	inicio VARCHAR, 
	conclusao VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (chamado_id), 
	FOREIGN KEY(chamado_id) REFERENCES chamados (id), 
	FOREIGN KEY(tecnico_id) REFERENCES usuarios (id)
);

CREATE INDEX IF NOT EXISTS ix_chamados_solicitante ON chamados(solicitante_id);
CREATE INDEX IF NOT EXISTS ix_chamados_tecnico ON chamados(tecnico_id);
CREATE INDEX IF NOT EXISTS ix_chamados_equipamento ON chamados(equipamento_id);
CREATE INDEX IF NOT EXISTS ix_chamados_status ON chamados(status);
CREATE INDEX IF NOT EXISTS ix_historico_chamado ON historico(chamado_id);
CREATE TABLE IF NOT EXISTS seed_versions (
    version VARCHAR PRIMARY KEY,
    aplicado_em VARCHAR NOT NULL
);
