const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function validId(value: unknown): boolean {
    return (typeof value === 'number' || typeof value === 'string')
        && /^[1-9]\d*$/.test(String(value))
        && Number.isSafeInteger(Number(value)) && Number(value) <= 2147483647;
}

export function validEquipmentIdentifier(value: unknown): boolean {
    return validId(value) || typeof value === 'string' && uuid.test(value);
}

export function equipmentPath(equipment: { id: unknown; public_id?: unknown }): string | null {
    const identifier = typeof equipment.public_id === 'string' && uuid.test(equipment.public_id)
        ? equipment.public_id : validId(equipment.id) ? equipment.id : null;
    return identifier === null ? null : '/equipamentos/' + identifier;
}

export function notificationDestination(notification: { destino: string | null; mensagem: string }): string | null {
    const legacyOrder = notification.destino === '/ordens' ? notification.mensagem.match(/\bOS-([1-9]\d*)\b/) : null;
    const destination = legacyOrder ? `/ordens?id=${legacyOrder[1]}` : notification.destino;
    if (!destination) return null;
    if (destination === '/ordens' || destination === '/preventivas') return destination;
    const equipment = destination.match(/^\/equipamentos\/([^/]+)$/);
    if (equipment) return validEquipmentIdentifier(equipment[1]) ? destination : null;
    const record = destination.match(/^\/(?:chamados\/|ordens\?id=)([1-9]\d*)$/);
    return record && validId(record[1]) ? destination : null;
}
