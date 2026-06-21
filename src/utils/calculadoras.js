/**
 * Calcula el tiempo de carga doméstica (AC) en horas.
 * @param {number} bateria - Capacidad de la batería en kWh.
 * @param {number} potenciaCargador - Potencia del cargador en kW.
 * @returns {number} Tiempo en horas.
 */
export const calcularTiempoDomestica = (bateria, potenciaCargador) => {
  if (potenciaCargador <= 0) return Infinity;
  return bateria / potenciaCargador;
};

/**
 * Calcula el coste de 100km en euros.
 * @param {number} consumo - Consumo en kWh/100km.
 * @param {number} precioKwh - Precio del kWh en euros.
 * @returns {number} Coste en euros.
 */
export const calcularCoste100km = (consumo, precioKwh) => {
  return consumo * precioKwh;
};

/**
 * Calcula el tiempo estimado de carga rápida (DC) del 10% al 80% en horas.
 * Asume una curva de carga promedio donde la potencia máxima se mantiene constante (simplificación).
 * @param {number} bateria - Capacidad de la batería en kWh.
 * @param {number} potenciaDcMax - Potencia máxima de carga en kW.
 * @returns {number} Tiempo en horas.
 */
export const calcularTiempoRapida = (bateria, potenciaDcMax) => {
  if (potenciaDcMax <= 0) return Infinity;
  // Cargamos el 70% de la batería (del 10% al 80%)
  const energiaACargar = bateria * 0.7;
  return energiaACargar / potenciaDcMax;
};
