<!---SECTION: Getting Familiar-->
Real-Time Feature Store: Fraud & Responsible Gambling with Apache Fluss
===

In this hands-on workshop you will build a **real-time feature store** for an online sports betting platform using **Apache Flink** and **Apache Fluss**. You'll compute 13 behavioural features from live betting events, keep them in a single Fluss primary-key table written by seven independent jobs at once, and serve them to two very different consumers: a Flink SQL risk-scoring pipeline and a Python REST service — both reading the same store, with no mirror and no lag.

The problem this solves is feature staleness. A fraud bot can place 25 bets in two minutes. A player chasing losses needs an intervention now, not in tomorrow's batch run. If your features are recomputed hourly, your rules are scoring a world that has already moved on — and no amount of threshold tuning fixes stale input.

A data generator is already running and publishing synthetic betting activity as JSON to four Kafka topics: `bets`, `bet_settlements`, `login_events` and `deposits`. Player profiles and wallets live in PostgreSQL and arrive in Flink through CDC. Your goal is to build the feature-engineering pipeline, wire up real-time scoring, then deliberately trigger fraud and responsible-gambling anomalies and watch the risk level flip within seconds.

The following tools and components are available in this environment:

- **Ververica**: access the Ververica Unified Streaming Data Platform web console to write and run Flink SQL jobs.
- **Redpanda**: inspect the four Kafka topics the generator produces to, and the `risk_scores` topic your pipeline will write.
- **Fraud Generator**: a click-to-fire UI (port 9050) that injects six different anomalous player behaviours on demand.
- **Scoring Service**: a Python REST service (port 9051) that looks features up from Fluss directly and scores a bet in single-digit milliseconds.
- **Grafana**: a real-time risk dashboard showing alert distribution, rule trigger frequency and end-to-end pipeline latency.

> [!NOTE]
> Use the following credentials to connect to the PostgreSQL database:
> - **User**: root
> - **Password**: admin1

> [!NOTE]
> Please skip any license messages you encounter in the different components. This lab environment is for training purposes only.

> [!NOTE]
> The SQL for every job in this lab has already been created for you as a **draft** in Ververica.
> Go to **SQL** → **Drafts** and you will find twelve of them, numbered in the order you should run them.
> You never need to type the long statements by hand — but do read them, because the whole point of the
> lab is what they do differently from a normal aggregation pipeline.

> [!WARNING]
> Drafts `3` through `12` contain **only** their own `INSERT` statement — no `CREATE CATALOG` or
> `CREATE TABLE`. They resolve their catalogs from the session, so you must run draft
> `1-ddl-sources-and-catalogs` and `2-ddl-player-feature-store` **first**, in the same SQL Editor
> session. If you skip them, later drafts fail with "Object not found".

<!---SECTION: Lab 1: The Online Feature Store-->
Lab 1: The Online Feature Store
===

In this lab you will register the Fluss catalog and the source tables, then create the one table this entire workshop revolves around: a primary-key table holding exactly one row per player, which seven jobs will write to concurrently.

### Step 1: Register the catalogs and source tables

Go to the **Ververica** tab, then navigate to **SQL** → **Drafts**. Open the draft named `1-ddl-sources-and-catalogs`.

This one script registers everything upstream of the feature store:

- the `fluss` catalog and the `fluss.betting` database
- a `betting_jdbc` catalog for writing an audit trail back to PostgreSQL
- `players_cdc` and `player_wallets_cdc` — `postgres-cdc` tables that snapshot PostgreSQL, then stream every subsequent change
- `bets`, `bet_settlements`, `login_events` and `deposits` — the four Kafka sources
- `risk_scores` — the Kafka sink your scoring job will write to

Click `Run` to execute the whole script. Every statement is DDL, so nothing long-running starts yet.

Note how the Fluss catalog is registered — it points at the coordinator's in-cluster address:

```sql,line-numbers,wrap
CREATE CATALOG fluss WITH (
  'type'              = 'fluss',
  'bootstrap.servers' = 'coordinator-server-0.coordinator-server-hs.fluss.svc.cluster.local:9124'
);
```

> [!NOTE]
> Keep this SQL Editor session open for the rest of the lab. Catalogs are session-scoped, and the job
> drafts you run later depend on them.

### Step 2: Look at the raw events

Before building anything, see what you're working with. Go to the **Redpanda** tab and open the `bets` topic.

Each message is a single wager:

```json
{
  "bet_id": "BET-3F9A2C1D04",
  "player_id": "P-3D6E9444",
  "amount": 42.50,
  "bet_type": "single",
  "sport": "football",
  "odds": 2.35,
  "event_time": "2026-08-03 09:28:33.716"
}
```

Nothing here says whether this player is a bot, is chasing losses, or is a sharp bettor. That is entirely a function of *behaviour over time* — which is what the feature store is for.

> [!NOTE]
> `event_time` is UTC. If Redpanda's console shows a record timestamp that looks a couple of hours off
> from the `event_time` field, that is your browser rendering the epoch in your local timezone — not a
> data problem. The whole stack runs in UTC.

### Step 3: Create the feature store table

Open the draft named `2-ddl-player-feature-store` and click `Run`.

This is the table everything else in the lab reads from or writes to:

```sql,line-numbers,wrap
CREATE TABLE IF NOT EXISTS fluss.betting.player_feature_store (
  player_id            STRING,

  -- Fraud / bot detection (10-min HOP, 10-sec slide)
  bets_last_10min      BIGINT,

  -- Responsible gambling (30-min HOP, 10-sec slide)
  total_stake_30min    DECIMAL(14,2),
  distinct_sports_30min BIGINT,

  -- Loss streak (event-driven, MATCH_RECOGNIZE)
  current_loss_streak  BIGINT,

  -- RG + fraud: live bet impulsivity (15-min HOP, 10-sec slide)
  live_bet_ratio_15min DOUBLE,

  -- Sharp bettor detection (15-min HOP, 10-sec slide)
  avg_odds_15min       DOUBLE,

  -- Fraud / multi-accounting (15-min HOP, 10-sec slide)
  geo_mismatches_15min BIGINT,

  -- Operator P&L exposure (30-min HOP, 10-sec slide)
  net_pnl_30min        DECIMAL(14,2),

  -- Dimensions from CDC
  kyc_tier             STRING,
  balance              DECIMAL(14,2),
  lifetime_deposits    DECIMAL(14,2),

  last_updated_at      TIMESTAMP(3),

  PRIMARY KEY (player_id) NOT ENFORCED
) WITH (
  'bucket.num' = '4'
);
```

Two things make this a *feature store* rather than just another table:

1. **`PRIMARY KEY (player_id)`** — one row per player, updated in place. Looking up a player's full feature vector is an O(1) hash lookup, not a scan or an aggregation.
2. **Different features come from different sources on different schedules.** `bets_last_10min` comes from a 10-minute window over `bets`; `current_loss_streak` is event-driven from `bet_settlements`; `kyc_tier` arrives via CDC from PostgreSQL. They have nothing in common except the key.

<!---SECTION: Lab 2: Feature Engineering — Seven Writers, One Row-->
Lab 2: Feature Engineering — Seven Writers, One Row
===

Here is where most feature-store designs get painful. Seven independent jobs need to write to one row per player. In a normal upsert sink, whichever job writes last wins and wipes out the others' work — so teams end up building one giant job that computes everything, which nobody can change without redeploying the lot.

Fluss avoids this with **partial column updates**: each job lists only the columns it owns in its `INSERT`, and Fluss updates just those columns, leaving the rest of the row untouched. Seven teams, seven deploy cycles, one row.

### Step 4: Start Job A — dimensions from CDC

Open the draft `3-job-feature-store-load`.

This job joins `players_cdc` with `player_wallets_cdc` and writes the three dimension columns: `kyc_tier`, `balance` and `lifetime_deposits`. It is the only job here that is not windowed — it fires whenever a row changes in PostgreSQL.

This is the first long-running job, so deploy it properly:

1. In the SQL Editor toolbar, click `Save As`. Keep the name `3-job-feature-store-load` — a self-descriptive name makes it easy to find again in **Deployments** once you have several jobs running.
2. In the new draft tab, click `Deploy`, then `Confirm` to create a SQL Deployment from it.
3. Go to **Deployments** in the left-hand menu, find the job, and click `Start` (with **Initial Mode** selected) to launch it.

> [!NOTE]
> On its first run this job takes a full snapshot of both PostgreSQL tables before anything reaches
> Fluss, so give it a moment. Once the snapshot completes it switches to streaming changes.

### Step 5: Start Job B1 — bet velocity, and the zero-fill pattern

Open `4-job-bet-velocity-calculation` and deploy it the same way (`Save As` → `Deploy` → `Confirm` → `Start`).

Read this one carefully, because the shape is not obvious:

```sql,line-numbers,wrap
INSERT INTO fluss.betting.player_feature_store (player_id, bets_last_10min, last_updated_at)
SELECT
  wide.player_id,
  COALESCE(feat.bets_last_10min, CAST(0 AS BIGINT)) AS bets_last_10min,
  wide.window_end                                    AS last_updated_at
FROM (
  SELECT player_id, window_end
  FROM TABLE(HOP(TABLE bets, DESCRIPTOR(event_ts), INTERVAL '10' SECONDS, INTERVAL '20' MINUTE))
  GROUP BY player_id, window_start, window_end
) AS wide
LEFT JOIN (
  SELECT player_id, CAST(COUNT(*) AS BIGINT) AS bets_last_10min, window_end
  FROM TABLE(HOP(TABLE bets, DESCRIPTOR(event_ts), INTERVAL '10' SECONDS, INTERVAL '10' MINUTE))
  GROUP BY player_id, window_start, window_end
) AS feat
ON wide.player_id = feat.player_id AND wide.window_end = feat.window_end;
```

Notice the `INSERT` names only three of the thirteen columns. That's the partial update.

The double window needs explaining. The inner 10-minute `HOP` computes the feature. But a windowed aggregation only emits rows for players who were *active* in that window — so when a bot stops betting, it simply stops producing rows, and its `bets_last_10min` would stay frozen at 25 forever. A feature that never decays is worse than no feature.

The outer 20-minute window is deliberately wider. Any player active in the last 20 minutes appears on the left side of the `LEFT JOIN`, and if they have no row in the 10-minute feature window, `COALESCE` writes a `0`. **Inactive players are actively reset instead of going stale.**

### Step 6: Start the remaining window jobs

Deploy these four the same way. Each writes a different slice of the same row:

| Draft | Feature columns written | Source |
|---|---|---|
| `5-job-live-ratio-odds-calculation` | `live_bet_ratio_15min`, `avg_odds_15min` | `bets` |
| `6-job-stake-sports-calculation` | `total_stake_30min`, `distinct_sports_30min` | `bets` |
| `7-job-net-pnl-calculation` | `net_pnl_30min` | `bet_settlements` |
| `9-job-geo-mismatches-calculation` | `geo_mismatches_15min` | `login_events` |

All four use the same wide-window zero-fill pattern you just read in Step 5.

### Step 7: Start Job C2 — loss streak with MATCH_RECOGNIZE

Open `8-job-loss-streak-calculation` and deploy it.

Some features aren't aggregations at all. "How many times has this player lost in a row?" is a *pattern* over an ordered sequence, and SQL can express it directly:

```sql,line-numbers,wrap
INSERT INTO fluss.betting.player_feature_store (player_id, current_loss_streak, last_updated_at)
SELECT
  player_id,
  CAST(streak_length AS BIGINT) AS current_loss_streak,
  last_event_ts                 AS last_updated_at
FROM bet_settlements
MATCH_RECOGNIZE (
  PARTITION BY player_id
  ORDER BY     event_ts
  MEASURES
    COUNT(L.player_id) AS streak_length,
    LAST(L.event_ts)   AS last_event_ts
  ONE ROW PER MATCH
  AFTER MATCH SKIP PAST LAST ROW
  PATTERN (L+ W)
  DEFINE
    L AS outcome = 'loss',
    W AS outcome <> 'loss'
) AS mr;
```

`PATTERN (L+ W)` reads as "one or more losses, followed by a non-loss". The streak length is emitted when the run ends. Doing this with window functions and self-joins would be considerably uglier.

> [!NOTE]
> Because the pattern only completes when the losing run breaks, this feature updates at the *end* of a
> streak rather than continuously. Keep that in mind in Lab 4 when you fire the `STREAK` archetype.

### Step 8: Verify the feature store is filling up

Go back to the SQL Editor. Paste and `Run`:

```sql,line-numbers,wrap
SELECT COUNT(*) FROM fluss.betting.player_feature_store;
```

You should see thousands of players. Now look at one full feature vector:

```sql,line-numbers,wrap
SELECT player_id, bets_last_10min, total_stake_30min, distinct_sports_30min,
       live_bet_ratio_15min, avg_odds_15min, kyc_tier, balance, last_updated_at
FROM fluss.betting.player_feature_store
LIMIT 10;
```

Every column in those rows was written by a different job. No job knows the others exist.

<!---SECTION: Lab 3: Real-Time Inference-->
Lab 3: Real-Time Inference
===

The feature store is populated. Now use it to score bets as they arrive — enriching each incoming bet with its player's current feature vector at the exact moment the bet is processed.

### Step 9: Understand the temporal lookup join

Open the draft `10-job-risk-score-kafka-sink` but **read it before deploying**.

The mechanism at its core is three lines:

```sql,line-numbers,wrap
FROM bets AS b
LEFT JOIN fluss.betting.player_feature_store FOR SYSTEM_TIME AS OF b.proc_time AS f
  ON b.player_id = f.player_id
```

`FOR SYSTEM_TIME AS OF b.proc_time` means "look this player up in the feature store as of the moment this bet is being processed". Not a snapshot, not a cached copy — the live store, at processing time. This is the point-in-time correctness a dedicated feature platform sells you, expressed in standard SQL against a table you already own.

The rules applied on top are plain `CASE` logic, evaluated top to bottom:

| `risk_level` | Triggered when | Rule codes |
|---|---|---|
| `FRAUD_HIGH` | `bets_last_10min > 8` OR `geo_mismatches_15min > 1` | `BOT_VELOCITY`, `GEO_MISMATCH` |
| `RG_ALERT` | `current_loss_streak >= 6` OR `live_bet_ratio_15min > 0.5` OR `distinct_sports_30min >= 4` | `LOSS_STREAK`, `HIGH_LIVE_RATIO`, `CHASING_LOSSES` |
| `SHARP_BETTOR` | `avg_odds_15min < 2` AND `bets_last_10min > 5` | `SHARP_ODDS_PATTERN` |
| `STAKE_LIMIT` | `total_stake_30min > 500.00` | `DAILY_LIMIT` |
| `NORMAL` | none of the above | — |

Because the rules are ordered, an earlier one shadows a later one — a bot placing 25 bets is reported as `FRAUD_HIGH` even though it also breaches the stake limit. The `risk_reasons` column keeps every code that fired, so nothing is lost for audit.

Now deploy and start the job.

### Step 10: Persist the alerts to PostgreSQL

Open `11-job-risk-score-pgsql-sink` and deploy it.

This job reads the `risk_scores` Kafka topic your previous job writes and appends every non-`NORMAL` score to `risk_score_log` in PostgreSQL, along with `enrichment_lag_ms` — the measured milliseconds from the original bet's `event_time` to the moment the score was produced.

> [!WARNING]
> Grafana in Lab 6 reads exclusively from `risk_score_log`. If you skip this step, the dashboard will
> stay empty even though the pipeline is working correctly.

### Step 11: Watch scores being produced

Go to the **Redpanda** tab and open the `risk_scores` topic. Every bet flowing through the platform now carries a risk verdict:

```json
{
  "bet_id": "BET-3F9A2C1D04",
  "player_id": "P-3D6E9444",
  "risk_level": "NORMAL",
  "risk_reasons": "",
  "enrichment_lag_ms": 284
}
```

Most traffic is `NORMAL` — as it should be, since the baseline generator simulates ordinary players. In the next lab you'll change that on purpose.

### Step 12: Check the pipeline latency

Back in the SQL Editor:

```sql,line-numbers,wrap
SELECT AVG(enrichment_lag_ms) AS avg_lag_ms,
       MAX(enrichment_lag_ms) AS max_lag_ms,
       COUNT(*)               AS scored
FROM betting_jdbc.betting.risk_score_log;
```

Expect an average in the low hundreds of milliseconds. That figure is the whole argument for this architecture: from a bet being placed to a fully-featured risk decision, faster than a page load.

<!---SECTION: Lab 4: Trigger the Anomalies and Watch the Features Move-->
Lab 4: Trigger the Anomalies and Watch the Features Move
===

Everything so far has run on ordinary traffic. Now inject the behaviours the rules were written to catch — and watch the feature vector change, live, as the events land.

This lab uses two tabs together: the **Fraud Generator** injects the behaviour, and the **Scoring Service** shows you the effect on the feature store as it happens. Open both before you start.

### Step 13: Set up the two tabs

Open the **Scoring Service** tab first. This is a small Python service that reads the feature store directly with the `pyfluss` client — an O(1) primary-key lookup, no Flink involved. Its UI has three parts you'll use:

- **Quick select** — one chip per outlier player (`BOT_001` "Bot velocity", `GEO_001` "Geo mismatch", `STREAK_001` "Loss streak", `LIVE_001` "High live ratio", `SHARP_001` "Sharp odds", `LIMIT_001` "Stake limit"). Clicking a chip loads that player.
- **Score a Player** (left card) — the live view. It has an **Auto-refresh every 2 s** toggle, on by default, which re-scores the selected player every two seconds. This is what lets you watch a feature move rather than polling by hand.
- **Kafka Stream** (right card) — every bet flowing through the platform, scored as it arrives.

Click the `BOT_001` chip now, while the bot is still idle. You should see a `NORMAL` badge, "no triggers", and a feature table where `bets_last_10min` is `0`. That is your baseline.

Now open the **Fraud Generator** tab in a second browser tab, so you can switch between the two without losing the auto-refresh.

### Step 14: Fire the bot and watch the vector change

In the **Fraud Generator**, click **Bot / Velocity**. Player `BOT_001` starts placing 25 bets over about two minutes, all at identical odds of 1.95 — machine-like behaviour no human produces.

Switch straight back to the **Scoring Service** tab and watch the left card refresh itself every two seconds. In sequence, you will see:

1. **`bets_last_10min` climbing** — 0, then 1, 3, 6… The 10-minute window slides every 10 seconds, so the number is never more than a few seconds behind the bets actually being placed.
2. **The badge flipping** from `NORMAL` to `FRAUD_HIGH`, the moment the count crosses 8.
3. **A `BOT_VELOCITY` chip appearing** in the reasons row.
4. **`bets_last_10min` highlighted** in the feature table — the UI marks which features actually triggered, so you can see the causal link rather than infer it.
5. **`response_time_ms` staying in single digits** the whole time. The store is being written to continuously and read at the same moment, without either side blocking the other.

Watch the **Kafka Stream** panel on the right too — `BOT_001` bets appear there scored `FRAUD_HIGH`, mixed in among the `NORMAL` traffic from the rest of the platform.

This is the whole point of the workshop in one screen: nothing was retrained, no threshold was touched, no batch job ran. The feature simply became true, and the verdict followed within seconds.

> [!NOTE]
> Leave the bot to finish, then keep watching. After about ten minutes of no further bets from
> `BOT_001`, `bets_last_10min` drops back to `0` and the badge returns to `NORMAL` — that is the
> zero-fill pattern from Step 5 actively resetting a stale feature, not the row simply expiring.

### Step 15: Confirm the same values in Flink and PostgreSQL

The Scoring Service reads Fluss over the Python client. Check that Flink sees exactly the same row. In the **Ververica** SQL Editor:

```sql,line-numbers,wrap
SELECT player_id, bets_last_10min, total_stake_30min, avg_odds_15min, last_updated_at
FROM fluss.betting.player_feature_store
WHERE player_id = 'BOT_001';
```

Compare `bets_last_10min` against what the Scoring Service just showed you. **They match** — same row, same store, two different readers.

Then look at the audit trail your PostgreSQL sink job has been writing:

```sql,line-numbers,wrap
SELECT bet_id, risk_level, risk_reasons, enrichment_lag_ms, score_time
FROM betting_jdbc.betting.risk_score_log
WHERE player_id = 'BOT_001'
ORDER BY score_time DESC
LIMIT 10;
```

Every bet after the threshold crossing is `FRAUD_HIGH` / `BOT_VELOCITY`, each with its own measured `enrichment_lag_ms`.

### Step 16: Fire the rest

Work through the remaining five archetypes the same way: click the matching **Quick select** chip in the Scoring Service, leave auto-refresh running, then fire the card in the Fraud Generator and watch which feature moves.

| Fraud Generator card | Quick-select chip | What it simulates | Feature that moves | Expected verdict |
|---|---|---|---|---|
| **Geo Mismatch** | `GEO_001` | Login from GB, then Brazil, inside the same 15-minute window | `geo_mismatches_15min` | `FRAUD_HIGH` / `GEO_MISMATCH` |
| **Loss Streak** | `STREAK_001` | 8 consecutive losses, rotating across all 8 sports | `current_loss_streak`, `distinct_sports_30min` | `RG_ALERT` / `LOSS_STREAK` + `CHASING_LOSSES` |
| **Live Bet Addict** | `LIVE_001` | 10 of 12 bets placed in-play, one every 8–10 seconds | `live_bet_ratio_15min` | `RG_ALERT` / `HIGH_LIVE_RATIO` |
| **Sharp Bettor** | `SHARP_001` | 8 bets at odds below 2, seconds apart | `avg_odds_15min` | `SHARP_BETTOR` / `SHARP_ODDS_PATTERN` |
| **Stake Limit Breach** | `LIMIT_001` | £7,000 wagered in a single session | `total_stake_30min` | `STAKE_LIMIT` / `DAILY_LIMIT` |

Each one exercises a different feature and a different rule, but the mechanism is identical every time — and you can see it happen in the highlighted cell of the feature table.

> [!NOTE]
> `Sharp Bettor` deliberately fires exactly 8 bets, not 9. One more would push `bets_last_10min` past 8
> and the `FRAUD_HIGH` rule would shadow the `SHARP_BETTOR` verdict entirely. Rule ordering has
> consequences, and this is a good illustration of why you keep every fired code in `risk_reasons`.

> [!NOTE]
> `Loss Streak` writes `current_loss_streak` only once the losing run ends — that is the
> `MATCH_RECOGNIZE` semantics from Step 7. Watching this one in the Scoring Service is instructive:
> the feature sits at `0` through the whole losing run, then jumps straight to `8` when the closing
> winning bet completes the pattern. Event-driven features do not ramp; they arrive.

<!---SECTION: Lab 5: One Store, Two Readers-->
Lab 5: One Store, Two Readers
===

You have now seen both consumers work. This lab is about why that matters architecturally, and about the API contract a model server or application backend would actually call.

### Step 17: Call the scoring API directly

The UI you used in Lab 4 is a thin wrapper over one REST call. Make it yourself from the **Web Shell**:

```bash
curl -s -X POST http://localhost:9051/score \
  -H "Content-Type: application/json" \
  -d '{"player_id": "BOT_001"}'
```

The response carries the verdict, the reasons, and the full feature vector that produced it:

```json
{
  "player_id": "BOT_001",
  "risk_level": "FRAUD_HIGH",
  "risk_reasons": ["BOT_VELOCITY"],
  "triggered_features": ["bets_last_10min"],
  "features": { "bets_last_10min": 25, "avg_odds_15min": 1.95, "kyc_tier": "BASIC", "...": "..." },
  "response_time_ms": 4.32
}
```

Returning the features alongside the verdict is deliberate: an analyst reviewing a flagged bet needs to know *why*, and a model needs the same vector to be reproducible. Look at `response_time_ms` — single digits, including the network hop.

There is also a lookup-only endpoint, with no scoring applied:

```bash
curl -s http://localhost:9051/features/BOT_001
```

### Step 18: Why one store matters

You have now read the same feature vector three ways: through the Flink temporal join in the scoring job, through the Python client in the Scoring Service UI, and through a plain SQL `SELECT` in Step 15. All three agreed.

That is not a coincidence, it is the design. There is exactly one place where `bets_last_10min` is defined — Job B1 — and one place where its value lives. Nothing is mirrored into a serving cache, so there is no window in which the online and offline views disagree, and no second definition to drift. Training-serving skew becomes structurally hard to introduce rather than something you monitor and hope about.

Contrast this with the usual shape: a batch job computing features for training, a separate stream or service recomputing "the same" features for serving, and a reconciliation process nobody trusts.

### Step 19: Confirm the service is healthy

If the Scoring Service ever shows empty feature tables, check this first:

```bash
curl -s http://localhost:9051/health
```

`fluss_ready` must be `true`. If it is `false`, the service failed to reach the Fluss coordinator at startup and never retries — and note that `/score` still answers `200` in that state, with `features: {}` and a verdict of `NORMAL`. A broken store looks deceptively like a quiet one, which is worth remembering when you build something like this yourself.

> [!NOTE]
> The **Kafka Stream** panel is fed by a background consumer inside the service itself, scoring every
> bet independently of your Flink job and publishing to its own topic. It keeps working even if the
> Flink scoring drafts were never started — a third reader of the same store, and a useful reminder
> that the store, not any one pipeline, is the shared contract.

<!---SECTION: Lab 6: Monitoring in Grafana-->
Lab 6: Monitoring in Grafana
===

### Step 20: Open the risk dashboard

Go to the **Grafana** tab and open the dashboard **Betting Features — Real-Time Risk Pipeline**. It refreshes every 5 seconds and reads from the `risk_score_log` table your PostgreSQL sink job populates.

The panels answer the questions an operations team actually asks:

- **Risk Category Distribution** and **Alerts per Minute** — what is firing, and is it accelerating
- **Rule Trigger Frequency** — which specific rules dominate, so you can tell a real pattern from a badly-tuned threshold
- **Top 10 Active Risk Players** — the queue a fraud analyst works through
- **Bot Velocity**, **Loss Streak** and **RG Alerts** counters — one stat tile per rule family
- **Avg Pipeline Latency** and **Pipeline Latency Over Time** — the end-to-end freshness budget, targeting under 500 ms

### Step 21: Watch an anomaly appear end to end

Go back to the **Fraud Generator** and fire an archetype you have not used recently — **Loss Streak** is the most visually obvious.

Then watch Grafana. Within seconds you should see the `RG_ALERT` slice grow in the distribution panel, `LOSS_STREAK` and `CHASING_LOSSES` climb in the rule-frequency chart, `STREAK_001` appear at the top of the active-players table, and the latency gauge stay flat in the low hundreds of milliseconds throughout.

That last detail is the one worth pausing on: the alert arrived quickly *and* the pipeline never fell behind while doing it.

Congrats, you have built a complete real-time feature store: thirteen features computed by seven independent Flink jobs writing partial column updates into a single Fluss primary-key table, served simultaneously to a SQL scoring pipeline via temporal lookup join and to a Python REST API via O(1) key lookup, with fraud and responsible-gambling anomalies detected within seconds of the behaviour occurring — and not one line of it depending on a proprietary feature platform.
