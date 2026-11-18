# eu-gas-storage-valuation

What is a seasonal gas storage worth at the Dutch TTF hub, how much of that value is the summer to
winter spread you can lock in today (intrinsic) and how much is the option to react to prices later
(extrinsic)? And what would the storage actually have earned in the gas years 2019/20 to 2025/26,
through the 2021-2022 gas crisis? A research study on open TTF price data with a linear program for
the intrinsic value and least-squares Monte Carlo for the full value.
v0.2 adds the fundamentals: how fast does German storage empty with the weather, and where can it
stand on 31 March 2027 after a fill of only 62% at the end of October 2026?

v0.3 adds the German gas balance: flows at every border, LNG send-out, production and storage on one
day-by-day table, checked against the official annual figures.

Related: [de-power-market-ppa](https://github.com/serikov-power-markets/de-power-market-ppa), where German
power, gas and carbon prices are cointegrated, and
[de-battery-multimarket](https://github.com/serikov-power-markets/de-battery-multimarket), the same
intrinsic versus flexibility question for a battery.

## The German gas balance (v0.3)

Daily balance from January 2023 to 3 November 2026: ENTSOG physical flows at the borders and production
points, GIE ALSI LNG send-out and GIE AGSI+ storage. Implied demand is imports minus exports plus
production, LNG and net storage withdrawal.

The ENTSOG platform reports the same physical gas several times, under each operator of a shared
pipeline and again at virtual interconnection points, so a plain sum gives Norway about 906 TWh in 2024
against about 415 TWh in the official figures. Each corridor is therefore counted once (`balance.CORRIDORS`).
The list was chosen on 2024; 2023 and 2025 are the check.

| TWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| Imports including LNG, this balance | 973.6 | 862.2 | 1019.4 |
| Imports, Bundesnetzagentur | 968 | 865 | 1031 |
| Exports, this balance | 182.8 | 92.0 | 255.6 |
| Exports, Bundesnetzagentur | 187 | 89 | 221 |
| Implied demand, this balance | 824.1 | 838.7 | 860.2 |
| Consumption, Bundesnetzagentur | 811.5 | 844 | 864 |
| Demand error | +1.6% | -0.6% | -0.4% |

Demand closes within 1.6%, but partly because errors offset: in 2025 exports are 35 TWh too high, mainly
at the Czech border (93 TWh here against about 57 officially), and LNG 12 TWh too low (ALSI 94 against 106).

**Storage carries the weather.** Over the heating seasons, demand rises 167 GWh/d per heating degree day,
and storage withdrawal rises 172 GWh/d. Pipeline imports and LNG barely respond within the day: Norway
+3, the Netherlands +7, LNG +1, while exports also rise by 9. Between the mildest and the coldest tenth of
days, demand rises by 2,286 GWh/d and storage withdrawal by 2,331 GWh/d.

| Winter (15 Oct to 31 Mar), TWh | 2023/24 | 2024/25 | 2025/26 |
|---|---|---|---|
| Norway | 207.4 | 214.1 | 223.4 |
| Netherlands | 111.0 | 119.8 | 119.9 |
| Belgium | 88.9 | 55.5 | 117.5 |
| LNG | 33.5 | 26.1 | 63.6 |
| Exports | 42.6 | 53.8 | 124.3 |
| Net supply without storage | 430.8 | 382.4 | 420.5 |
| Storage withdrawal | 84.2 | 172.6 | 136.0 |
| Implied demand | 515.2 | 555.0 | 556.6 |
| Mean heating degree days | 12.09 | 13.07 | 13.52 |

**Why the weather model missed 2024/25.** The held-out test of v0.2 missed the 31 March 2025 fill by 24
points and pointed to supply. The balance shows it: net supply was 43 TWh below the mean of the two
neighboring winters, about 17 points of German working gas volume, with Belgium and LNG lower and exports
slightly higher. 2025/26 was colder, yet took less from storage, because LNG rose by 38 TWh and Belgium
by 62 TWh, while exports rose by 71 TWh.

Limits: a balance of reported flows, not a supply forecast or a stack model with prices. Line pack, biogas
and metering differences stay in implied demand. The slopes are descriptive associations over three
winters. Storage connected across a border (Haidach, Epe and others) is taken from AGSI+ only. No vessel
tracking, outages or capacity constraints. One day has negative implied demand, which shows the noise in
single-day values. LNG send-out for the balance comes from ALSI.

## Results

Facility: 1 TWh working gas volume, full in 150 days, empty in 75 days, variable costs 0.25 EUR/MWh
injected and 0.10 EUR/MWh withdrawn, empty at the start and end of the storage year. Values are in
EUR per MWh of working gas volume, discounted at 2.5%.

### Value for the storage year April 2027 to March 2028 (valued on 28 October 2026)

The forward curve is illustrative (see Model): the front month on the valuation date (99.90 EUR/MWh)
scaled by a seasonal shape estimated from history, whose depth is varied below. Spot model:
kappa 2.9 per year (half-life 87 days), sigma 0.74, calibrated on April 2023 to October 2026.

| Winter minus summer on the curve (EUR/MWh) | Intrinsic | Total (LSMC) | Extrinsic |
|---|---|---|---|
| 0 (flat curve) | 0.0 | 17.0 | 17.0 |
| 5.1 | 5.9 | 18.7 | 12.9 |
| 9.8 | 12.4 | 21.6 | 9.2 |
| 17.9 (full estimated shape) | 24.1 | 29.1 | 5.0 |

Monte Carlo standard errors are about 0.5 (2,000 paths; 0.26 for the full shape with 8,000).

| Volatility sigma | kappa 1 | kappa 3 | kappa 10 |
|---|---|---|---|
| 0.25 | 0.3 | 0.7 | 1.0 |
| 0.50 | 0.8 | 2.4 | 3.2 |
| 0.75 | 1.8 | 5.2 | 7.0 |
| 1.00 | 3.2 | 8.8 | 11.7 |

Extrinsic value with the full estimated shape, by volatility and mean reversion.

| Facility (days to fill / to empty) | Intrinsic | Total | Extrinsic |
|---|---|---|---|
| Seasonal 150 / 75 | 24.1 | 29.1 | 5.0 |
| Medium 60 / 30 | 28.2 | 36.9 | 8.6 |
| Fast-cycle 20 / 10 | 28.6 | 43.6 | 15.0 |

Findings:

- **Intrinsic and extrinsic value substitute for each other.** A flatter curve removes intrinsic
  value but raises extrinsic value, because the owner keeps the freedom to cycle on price swings
  instead of being committed to one summer to winter trade. Over the range tested the intrinsic
  value falls by 24 EUR/MWh, the total only by 12.
- **The extrinsic value is a volatility and mean-reversion bet.** It ranges from 0.3 to 11.7
  EUR/MWh over plausible parameters. Faster mean reversion raises it: price deviations close within
  the storage year, so buying low and selling high pays more often.
- **Flexibility is worth most as optionality.** The same volume with ten times the injection and
  withdrawal rates gains only 4.5 EUR/MWh of intrinsic value but three times the extrinsic value.

### Backtest: unhedged storage trading in past gas years

On 31 March of each year the curve and the spot model are estimated from earlier data only, the
policy is trained on simulated paths and then executed on the realised TTF path. No futures hedge.

| Gas year | Price 31 March | Curve spread | Perfect foresight | Calendar rule | LSMC policy |
|---|---|---|---|---|---|
| 2019/20 | 14.22 | 0.5 | 3.7 | -0.6 | -0.2 |
| 2020/21 | 6.90 | 1.6 | 13.0 | 12.0 | 8.2 |
| 2021/22 | 19.00 | 7.0 | 95.7 | 65.6 | 36.1 |
| 2022/23 | 125.91 | 45.7 | 91.4 | -57.1 | -39.5 |
| 2023/24 | 47.85 | 17.4 | 13.7 | -2.1 | -1.8 |
| 2024/25 | 27.34 | 10.0 | 17.2 | 14.6 | 11.9 |
| 2025/26 | 40.67 | 13.7 | 12.9 | -3.6 | -3.2 |
| **Sum** | | | **247.6** | **28.8** | **11.5** |

Calendar rule: inject from 1 April until full, withdraw from 1 December until empty.

- **Without a hedge the result is a bet on the price level.** The calendar rule earned 65.6 in
  2021/22, when prices rose through the year, and lost 57.1 in 2022/23, when gas bought at crisis
  prices in summer was sold after the collapse. Four of seven years were losses.
- **The LSMC policy loses less in falling markets and earns less in rising ones.** It beat the
  calendar rule in the four loss years and trailed it in the three profitable ones; summed over the
  seven years it earned 11.5 against 28.8. It reacts to price moves the model treats as temporary,
  which hurts when they persist (2021/22).
- **The value is captured by hedging.** Perfect foresight shows 248 EUR/MWh was available; a storage
  owner secures the spread by selling winter and buying summer futures on day one and then
  re-optimises against the curve. Doing that needs historical forward curves, which are not open
  data (see Next).

The realised winter minus summer spread of the front month was positive in six of the eight
complete gas years from 2018/19 and negative in 2022/23 (-25.7 EUR/MWh) and 2025/26 (-4.3).

![TTF and seasonality](figures/ttf_seasonality.png)
![Backtest](figures/backtest_gas_years.png)
![Intrinsic schedule](figures/intrinsic_schedule.png)
![Realised seasonal spread](figures/realised_seasonal_spread.png)

### v0.2: German storage fundamentals and the coming winter

Daily net withdrawal from German storage (GIE AGSI+) against population-weighted heating degree
days (ERA5), fitted on the four heating seasons since Russian pipeline supply ended (2022/23 to
2025/26). Each extra heating degree day raises withdrawal by 173 GWh/d (same and previous day);
weekends are 437 GWh/d lower.

| Held-out winter | Daily error (GWh/d) | ... without weather | Fill 31 March: actual | model | without weather |
|---|---|---|---|---|---|
| 2022/23 | 394 | 709 | 64.1 | 46.6 | 42.3 |
| 2023/24 | 267 | 574 | 62.8 | 58.1 | 47.4 |
| 2024/25 | 425 | 616 | 28.7 | 53.1 | 57.9 |
| 2025/26 | 322 | 568 | 22.2 | 19.6 | 31.8 |

Each winter is predicted by a model fitted on the other three, from its real fill on 15 October
with its real weather. Weather halves the daily error (352 against 617 GWh/d) and cuts the mean
error of the 31 March fill from 19.0 to 12.3 percentage points. The rest is supply: in 2024/25
the model missed by 24 points.

**Scenarios for winter 2026/27.** On 27 October 2026 German storage held 152.7 TWh, 61.7% of its
247.4 TWh working volume, below the 1 November level of every year since 2012 (lowest before:
72.7% in 2021). The temperatures of all 35 winters 1991/92 to 2025/26, shifted to today's climate
by the warming trend, are run through the model with the residuals of each of the four fitted
winters (140 scenarios), and withdrawal is capped by the deliverability observed at each fill.

| Fill (%) | 5% | 25% | Median | 75% | 95% |
|---|---|---|---|---|---|
| 1 February 2027 | 13.6 | 21.1 | 29.1 | 38.4 | 46.1 |
| 31 March 2027 | 3.5 | 6.8 | 14.1 | 22.8 | 35.3 |

- With the supply of the last four winters and no price response, storage ends the winter below
  30% in 88% of scenarios, below 20% in 66% and below 10% in 39%. Replaying the cold winter of
  1995/96 leaves 2.9%.
- Supply matters as much as weather: with the residuals of 2022/23 the median ends at 26.5%, with
  those of 2024/25 at 5.7%.
- Without the warming adjustment (temperatures as observed) the median falls to 7.4%.
- The scenarios hold prices and supply behaviour fixed, so they describe the gap the market has to
  close with more LNG imports or lower demand, not a forecast. A high winter price is how that gap
  closes; the TTF front month stood near 100 EUR/MWh on the valuation date.

![Storage scenarios](figures/storage_fill_scenarios.png)

## Model

- **Storage and weather (v0.2):** GIE AGSI+ daily data for Germany (free API key); daily mean
  2 m temperature from ERA5 via the Open-Meteo archive at the ten largest cities, weighted by
  population; heating degree days 18 - T below 15 C (Eurostat). Ordinary least squares with month
  effects; deliverability is the 99th percentile of observed withdrawal in 5% fill bins, falling
  linearly to zero below the lowest observed fill.
- **Prices:** daily closes of the continuous TTF front-month future (Yahoo Finance, TTF=F, from
  October 2017), used as a spot proxy: on each day it is the price for delivery next month.
- **Seasonal shape:** log price minus a centred one-year rolling mean, averaged by delivery month,
  excluding September 2021 to March 2023. Winter months trade up to 21% above the annual mean,
  June to August about 15% below.
- **Forward curve:** the front month on the valuation date scaled by the seasonal factors. A real
  settlement curve can be supplied as a CSV (`curve.read_curve_csv`).
- **Intrinsic value:** linear program over daily injection and withdrawal against the forward curve
  (SciPy, HiGHS), rate limits, inventory bounds, start and end inventory.
- **Spot model:** one-factor mean-reverting log price around the forward curve (Schwartz 1997),
  E[S(t)] = F(t). kappa and sigma from an AR(1) of the deseasonalised log price on trading days.
- **Full value:** least-squares Monte Carlo (Boogert and de Jong 2008). Inventory on a grid of one
  day of full injection, cubic polynomials in the price as regressors, separate regressions per
  inventory level, decisions restricted to those that can still reach the end inventory. The
  policy is estimated on one set of paths and valued on an independent set, so the reported value
  is a lower bound of the model value up to Monte Carlo error. With zero volatility it reproduces
  the intrinsic value (tested).

## Limitations

- The forward curve is constructed, not observed. The estimated seasonal shape comes from realised
  prices and is deeper than typical traded spreads, which is why the value is reported over the
  spread rather than as one number.
- The front month is not day-ahead gas: it moves less day to day and jumps at contract rolls. One
  price factor only; real curves move in level and in spread separately.
- Constant injection and withdrawal rates (no ratchets that depend on the fill level), no
  capacity cost, no bid-ask spread or market impact, no storage regulation (fill-level targets).
- v0.2 has no price feedback, one country and no cross-border storage use (German storage also
  serves neighbours); the supply regime is estimated from four winters only.
- Illustrative research study on public data; not a commercial valuation or supply forecast.

## Next

- LNG send-out (GIE ALSI) and pipeline flows (ENTSOG) as explicit supply terms, and the link from
  the storage outlook to the winter-summer spread.
- v0.3: rolling intrinsic and a hedged backtest, fill-dependent ratchets, two-factor spot model.

## Run

```bash
pip install -e ".[test]"
pytest -q                  # offline, synthetic data
python -m gasstor.run      # downloads TTF prices, writes results/ and figures/ (about 10 minutes)
export AGSI_KEY=...        # free key from agsi.gie.eu
python -m gasstor.fundamentals_run   # storage model and winter scenarios (results/fundamentals/)
```
