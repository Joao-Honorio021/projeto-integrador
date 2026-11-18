import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/services/navigation.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
const { equipmentPath, validId, validEquipmentIdentifier, notificationDestination } = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));

for (const value of [null, undefined, '', 'null', 'undefined', 'invalid', 0, -1, 1.5, '1/2', '1e3', true, 2147483648]) {
    test(`rejeita identificador inválido: ${String(value)}`, () => {
        assert.equal(validId(value), false);
        assert.equal(validEquipmentIdentifier(value), false);
    });
}

test('equipamento legado usa seu ID real quando o UUID está ausente ou inválido', () => {
    for (const public_id of [null, undefined, '', 'null', 'undefined', 'invalid', 5]) {
        assert.equal(equipmentPath({ id: 42, public_id }), '/equipamentos/42');
    }
    assert.equal(equipmentPath({ id: null, public_id: null }), null);
    assert.equal(equipmentPath({ id: 'undefined' }), null);
});

test('preserva UUID de etiquetas existentes e aceita o ID numérico', () => {
    const uuid = '9dd33bb0-5059-4ee5-8d08-7cda514c8ea4';
    assert.equal(equipmentPath({ id: 42, public_id: uuid }), `/equipamentos/${uuid}`);
    assert.equal(validEquipmentIdentifier(uuid), true);
    assert.equal(validId('42'), true);
    assert.equal(validId(42), true);
});

test('notificações navegam ao recurso específico, incluindo ordens legadas', () => {
    for (const destino of ['/equipamentos/42', '/chamados/37', '/ordens?id=81', '/preventivas']) {
        assert.equal(notificationDestination({ destino, mensagem: 'Evento' }), destino);
    }
    assert.equal(notificationDestination({ destino: '/ordens', mensagem: 'Ordem OS-81 atribuída' }), '/ordens?id=81');
});

test('notificações não produzem links externos, inválidos ou indisponíveis', () => {
    for (const destino of [null, '', '/equipamentos/null', '/chamados/undefined', '/ordens?id=0',
        '/ordens?id=2147483648', 'https://example.org', '//example.org', 'javascript:alert(1)',
        '/equipamentos/42?redirect=https://example.org', '/chamados/42/editar']) {
        assert.equal(notificationDestination({ destino, mensagem: 'Evento' }), null);
    }
});
