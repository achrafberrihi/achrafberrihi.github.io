// Power Query (M) — load the pipeline outputs.
// Set DataFolder to the absolute path of data/powerbi on your machine.
let
    DataFolder = "C:\Projects\Air_Quality_Anomaly_PowerBI\data\powerbi\",

    LoadCsv = (name as text) as table =>
        let
            Source = Csv.Document(File.Contents(DataFolder & name), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
            Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
        in
            Promoted,

    Readings = Table.TransformColumnTypes(LoadCsv("fact_readings.csv"), {
        {"timestamp", type datetime}, {"sensor_id", type text},
        {"co2_ppm", type number}, {"pm25_ugm3", type number}, {"tvoc_ppb", type number},
        {"temp_c", type number}, {"humidity_pct", type number}, {"iforest_score", type number},
        {"flag_spike", type logical}, {"flag_stuck", type logical}, {"flag_drift", type logical},
        {"flag_iforest", type logical}, {"flag_threshold", type logical},
        {"is_anomaly", type logical}, {"detected_type", type text}}),
    WithDate = Table.AddColumn(Readings, "date", each DateTime.Date([timestamp]), type date)
in
    WithDate

// Repeat LoadCsv for fact_alerts.csv (start/end as datetime), fact_forecast.csv and dim_sensor.csv,
// then create a Date table: Date = CALENDAR(MIN(fact_readings[date]), MAX(fact_readings[date])).
