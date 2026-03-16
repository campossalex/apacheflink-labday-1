
```
python3 flights.py --broker kubernetes-vm:9092 --topic flights


CREATE TABLE `vvp`.`default`.`flights_events` (
  `id` VARCHAR(2147483647),
  `airportIataCode` VARCHAR(2147483647),
  `airportIcaoCode` VARCHAR(2147483647),
  `movementType` VARCHAR(2147483647),
  `sourceUpdated` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `airlineIcaoCode` VARCHAR(2147483647),
  `airlineIataCode` VARCHAR(2147483647),
  `flightNumber` INT,
  `flightOperationalSuffix` VARCHAR(2147483647),
  `operatingAirlineCode` VARCHAR(2147483647),
  `publicFlightCode` VARCHAR(2147483647),
  `callSign` VARCHAR(2147483647),
  `coordinated` BOOLEAN,
  `initialSchedule` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `initialOperationalSuffix` VARCHAR(2147483647),
  `references` ROW<`AODB` VARCHAR(2147483647), `FUB` VARCHAR(2147483647)>,
  `associatedFlight` ROW<`sequence` VARCHAR(2147483647), `id` VARCHAR(2147483647), `airlineIcaoCode` VARCHAR(2147483647), `airlineIataCode` VARCHAR(2147483647), `flightNumber` INT, `flightOperationalSuffix` VARCHAR(2147483647), `publicFlightCode` VARCHAR(2147483647), `schedule` TIMESTAMP(3) WITH LOCAL TIME ZONE, `references` ROW<`AODB` VARCHAR(2147483647), `FUB` VARCHAR(2147483647)>>,
  `operationalStatus` VARCHAR(2147483647),
  `remark` VARCHAR(2147483647),
  `departureAirportIataCode` VARCHAR(2147483647),
  `departureAirportIcaoCode` VARCHAR(2147483647),
  `arrivalAirportIataCode` VARCHAR(2147483647),
  `arrivalAirportIcaoCode` VARCHAR(2147483647),
  `serviceType` VARCHAR(2147483647),
  `nature` INT,
  `operationType` INT,
  `classification` VARCHAR(2147483647),
  `aircraftTypeIata` VARCHAR(2147483647),
  `aircraftTypeIcao` VARCHAR(2147483647),
  `registration` VARCHAR(2147483647),
  `seatCapacity` INT,
  `wakeTurbulenceCategory` VARCHAR(2147483647),
  `standardInstrumentDeparture` VARCHAR(2147483647),
  `standardArrivalRoute` VARCHAR(2147483647),
  `flightRules` VARCHAR(2147483647),
  `matchCode` VARCHAR(2147483647),
  `scheduledTimeOfArrival` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `scheduledTimeOfDeparture` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `estimatedTimeOfDeparture` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualOffBlockOfDeparture` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualTakeOffOfDeparture` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `targetLanding` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `estimatedLanding` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `tenMilesOut` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualLanding` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `scheduledInBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `estimatedInBlock` ROW<`AIRLINE` TIMESTAMP(3) WITH LOCAL TIME ZONE, `ACDM` TIMESTAMP(3) WITH LOCAL TIME ZONE>,
  `actualInBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `scheduledOffBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `estimatedOffBlock` ROW<`AIRLINE` TIMESTAMP(3) WITH LOCAL TIME ZONE, `NETWORK_MANAGER` TIMESTAMP(3) WITH LOCAL TIME ZONE, `ATC` TIMESTAMP(3) WITH LOCAL TIME ZONE, `AODB` TIMESTAMP(3) WITH LOCAL TIME ZONE>,
  `actualOffBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `targetOffBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `calculatedOffBlock` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `targetStartupApproval` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualStartup` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualStartupStatus` VARCHAR(2147483647),
  `estimatedTakeOff` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `targetTakeOff` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `calculatedTakeOff` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualTakeOff` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualGroundHandlingCommence` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualStartupRequest` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `actualReady` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `estimatedTaxiIn` VARCHAR(2147483647),
  `estimatedTaxiOut` VARCHAR(2147483647),
  `totalPassengersCount` INT,
  `transferPassengersCount` INT,
  `localPassengersCount` INT,
  `webCheckInCount` INT,
  `onSiteCheckInCount` INT,
  `prmAssistancesTotal` INT,
  `prmAssistancesTotalNotified` INT,
  `prmAssistancesTotalNonNotified` INT,
  `securityQueuePaxEntryTotal` INT,
  `securityQueuePaxExitTotal` INT,
  `firstCrewMemberPassage` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `lastCrewMemberPassage` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `irregularityDelays` MAP<VARCHAR(2147483647), VARCHAR(2147483647)>,
  `runwayCode` VARCHAR(2147483647),
  `runwayExit` VARCHAR(2147483647),
  `runwayIntersection` VARCHAR(2147483647),
  `standCode` VARCHAR(2147483647),
  `standHandler` VARCHAR(2147483647),
  `terminals` MAP<VARCHAR(2147483647), VARCHAR(2147483647)>,
  `gates` MAP<VARCHAR(2147483647), ROW<`terminal` VARCHAR(2147483647), `handler` VARCHAR(2147483647), `gateAt` TIMESTAMP(3) WITH LOCAL TIME ZONE, `goToGate` TIMESTAMP(3) WITH LOCAL TIME ZONE, `gateOpen` TIMESTAMP(3) WITH LOCAL TIME ZONE, `boarding` TIMESTAMP(3) WITH LOCAL TIME ZONE, `finalCall` TIMESTAMP(3) WITH LOCAL TIME ZONE, `gateClosed` TIMESTAMP(3) WITH LOCAL TIME ZONE, `publicGate` VARCHAR(2147483647), `status` VARCHAR(2147483647), `boardingAlarms` VARCHAR(2147483647)>>,
  `baggageClaimBelts` MAP<VARCHAR(2147483647), ROW<`terminal` VARCHAR(2147483647), `handler` VARCHAR(2147483647), `firstBag` TIMESTAMP(3) WITH LOCAL TIME ZONE, `lastBag` TIMESTAMP(3) WITH LOCAL TIME ZONE, `firstBagAt` TIMESTAMP(3) WITH LOCAL TIME ZONE, `status` VARCHAR(2147483647)>>,
  `checkinCounters` MAP<VARCHAR(2147483647), ROW<`terminal` VARCHAR(2147483647), `handler` VARCHAR(2147483647), `open` TIMESTAMP(3) WITH LOCAL TIME ZONE, `close` TIMESTAMP(3) WITH LOCAL TIME ZONE, `status` VARCHAR(2147483647)>>,
  `chutes` MAP<VARCHAR(2147483647), ROW<`terminal` VARCHAR(2147483647), `handler` VARCHAR(2147483647), `open` TIMESTAMP(3) WITH LOCAL TIME ZONE, `close` TIMESTAMP(3) WITH LOCAL TIME ZONE, `status` VARCHAR(2147483647)>>,
  `intermediateStops` MAP<VARCHAR(2147483647), ROW<`airportIataCode` VARCHAR(2147483647), `airportIcaoCode` VARCHAR(2147483647)>>,
  `codeShares` MAP<VARCHAR(2147483647), ROW<`airlineIcaoCode` VARCHAR(2147483647), `airlineIataCode` VARCHAR(2147483647), `flightNumber` INT, `flightOperationalSuffix` VARCHAR(2147483647), `publicFlightCode` VARCHAR(2147483647)>>,
  `created` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `createdBy` VARCHAR(2147483647),
  `updated` TIMESTAMP(3) WITH LOCAL TIME ZONE,
  `updatedBy` VARCHAR(2147483647),
  `kafka_topic` VARCHAR(2147483647) METADATA FROM 'topic' VIRTUAL,
  `kafka_partition` INT METADATA FROM 'partition' VIRTUAL,
  `kafka_offset` BIGINT METADATA FROM 'offset' VIRTUAL,
  `kafka_timestamp` TIMESTAMP(3) WITH LOCAL TIME ZONE METADATA FROM 'timestamp' VIRTUAL,
  WATERMARK FOR `sourceUpdated` AS `sourceUpdated` - INTERVAL '10' SECOND
)
COMMENT ''
WITH (
  'connector' = 'kafka',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false',
  'json.timestamp-format.standard' = 'ISO-8601',
  'properties.bootstrap.servers' = 'host.minikube.internal:9092',
  'properties.group.id' = 'flink-flights-consumer',
  'scan.startup.mode' = 'earliest-offset',
  'topic' = 'flights'
);


-- 1. Latest flight status per airport

SELECT
airportIataCode,
movementType,
airlineIataCode,
flightNumber,
operationalStatus,
sourceUpdated
FROM flights_events;

-- 2. Departures with delay codes
SELECT
`id`,
airportIataCode,
airlineIataCode || CAST(flightNumber AS STRING)  AS flight,
departureAirportIataCode,
arrivalAirportIataCode,
irregularityDelays
FROM flights_events
WHERE movementType = 'DEPARTURE'
AND irregularityDelays IS NOT NULL;

-- 3. filter for flight status


SELECT
    `movementType` as flight_type,
    `airlineIataCode` as airline_code,
    `flightNumber` as flight_number,
    departureAirportIataCode as origin,
    arrivalAirportIataCode as destination,  
    CAST(
        CASE `movementType`
            WHEN 'ARRIVAL'   THEN `scheduledInBlock`
            WHEN 'DEPARTURE' THEN `scheduledOffBlock`
            ELSE COALESCE(`scheduledInBlock`, `scheduledOffBlock`)
        END
    AS DATE)                                                        AS flight_date
FROM flights_events 
WHERE movementType IN('ARRIVAL', 'DEPARTURE');
```
