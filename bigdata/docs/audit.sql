-- Chạy sau khi tạm dừng và gửi hết bản ghi đã đến hạn.
SELECT sum(input) AS input, sum(clean) AS clean, sum(quarantine) AS quarantine,
       sum(duplicates) AS duplicate, sum(late) AS late, max(latency_ms) AS max_latency_ms
FROM microbatch;

WITH totals AS (
  SELECT bin,sum(generated_g)-sum(collected_g) AS net FROM daily GROUP BY bin
)
SELECT count(*) FILTER (WHERE p.grams<>coalesce(t.net,0)) AS bins_with_mass_difference
FROM physical_bin p LEFT JOIN totals t USING(bin);

SELECT (SELECT coalesce(sum(collected_g),0) FROM daily) -
       (SELECT coalesce(sum(load_g+dumped_g),0) FROM truck) AS vehicle_mass_difference_g;

SELECT month,status,count(*),sum(total_vnd) FROM invoice_status GROUP BY 1,2 ORDER BY 1,2;
SELECT status,reason,count(*) FROM payment_attempt GROUP BY 1,2 ORDER BY 1,2;

SELECT count(*) AS invoices_with_wrong_total FROM invoice i
WHERE total_vnd <> base_vnd + (SELECT sum((x->>'cost')::int) FROM jsonb_array_elements(i.detail) x);

SELECT count(*) AS invoices_with_wrong_mass
FROM invoice i JOIN bin b ON b.house=i.house
CROSS JOIN LATERAL jsonb_array_elements(i.detail) AS detail
WHERE detail->>'category'=b.category AND (detail->>'grams')::bigint <>
  (SELECT coalesce(sum(d.collected_g),0) FROM daily d
   WHERE d.bin=b.id AND d.day>=i.month AND d.day<i.month+interval '1 month');

SELECT count(*) AS wrong_payment_amounts FROM payment_attempt p JOIN invoice i ON p.invoice_ref=i.id
WHERE p.status='matched' AND (p.amount<>i.total_vnd OR p.house<>i.house);

SELECT month,result,count(*) FROM plan GROUP BY 1,2 ORDER BY 1,2;
SELECT date_trunc('minute',occurred AT TIME ZONE 'Asia/Ho_Chi_Minh') AS simulated_minute,
       count(*) AS peak_measurements_in_clean
FROM event WHERE payload->'data'->>'state'='peak' GROUP BY 1 ORDER BY 1;

SELECT house,month,status,issued,suspend_from,paid_at
FROM invoice_status WHERE month='2026-10-01' AND house IN ('H-0001','H-0002','H-0004','H-0020')
ORDER BY house;

SELECT count(*) AS pickups_during_suspension
FROM event e JOIN bin b ON b.id=e.subject JOIN invoice_status i ON i.house=b.house
WHERE e.kind='pickup' AND i.month='2026-10-01' AND i.house IN ('H-0001','H-0020')
  AND (e.occurred AT TIME ZONE 'Asia/Ho_Chi_Minh')::date>=i.suspend_from
  AND (i.paid_at IS NULL OR e.occurred<i.paid_at);

