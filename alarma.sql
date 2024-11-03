CREATE DATABASE IF NOT EXISTS alarma;
USE alarma;

-- Crear la tabla 'movimientos'
CREATE TABLE `movimientos` (
  `id` int NOT NULL AUTO_INCREMENT,                     -- Campo para el identificador único, autoincremental
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,       -- Campo para registrar la fecha y hora, con valor por defecto
  `descripcion` varchar(255) DEFAULT NULL,              -- Campo para la descripción, puede ser NULL
  PRIMARY KEY (`id`)                                    -- Definir 'id' como clave primaria
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
