<?php
// api/plaid.php — minimal backend for Plaid Link (local use only)
header("Content-Type: application/json; charset=utf-8");
if (!in_array($_SERVER["REMOTE_ADDR"] ?? "", ["127.0.0.1","::1"])) { http_response_code(403); echo json_encode(["error"=>"forbidden"]); exit; }

$cfgPath = __DIR__ . "/../python/config.ini";
$ini = parse_ini_file($cfgPath, true, INI_SCANNER_TYPED);
$plaid = $ini["plaid"] ?? [];
$env = strtolower($plaid["environment"] ?? "sandbox");
$base = $env === "production" ? "https://production.plaid.com" : ($env === "development" ? "https://development.plaid.com" : "https://sandbox.plaid.com");
$client_id = $plaid["client_id"] ?? "";
$secret    = $plaid["secret"] ?? "";
$redirect  = $plaid["redirect_uri"] ?? "";

if ($_SERVER["REQUEST_METHOD"] !== "POST") { http_response_code(405); echo json_encode(["error"=>"method_not_allowed"]); exit; }
$raw = file_get_contents("php://input");
$in  = $raw ? json_decode($raw, true) : [];
$action = $in["action"] ?? "";

function plaid_post($url, $body){
  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ["Content-Type: application/json"],
    CURLOPT_POSTFIELDS => json_encode($body, JSON_UNESCAPED_SLASHES),
    CURLOPT_TIMEOUT => 30
  ]);
  $res = curl_exec($ch);
  if ($res === false) { throw new Exception("curl_error: ".curl_error($ch)); }
  $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);
  $j = json_decode($res, true);
  if ($code < 200 || $code >= 300) { throw new Exception("Plaid error $code: ".($res ?: "unknown")); }
  return $j;
}

try {
  if ($action === "create_link_token") {
    $body = [
      "client_id" => $client_id,
      "secret"    => $secret,
      "client_name" => "Lingua Ink Dashboard",
      "language"    => "en",
      "country_codes"=> ["US"],
      "products"     => ["transactions"],
      "redirect_uri" => $redirect,
      "user" => [ "client_user_id" => "local-" . uniqid() ]
    ];
    $j = plaid_post("$base/link/token/create", $body);
    echo json_encode(["link_token"=>$j["link_token"] ?? null]); exit;
  }

  if ($action === "exchange_public_token") {
    $public_token = $in["public_token"] ?? "";
    if (!$public_token) throw new Exception("missing public_token");
    $j = plaid_post("$base/item/public_token/exchange", [
      "client_id"=>$client_id, "secret"=>$secret, "public_token"=>$public_token
    ]);
    $access = $j["access_token"] ?? "";
    if (!$access) throw new Exception("no access_token");

    // Write access_token back into config.ini
    $lines = file($cfgPath, FILE_IGNORE_NEW_LINES);
    $out = []; $in_plaid = false; $wrote = false;
    foreach ($lines as $line) {
      if (preg_match('/^\s*\[plaid\]\s*$/i', $line)) { $in_plaid = true; $out[] = $line; continue; }
      if ($in_plaid && preg_match('/^\s*\[/', $line)) { $in_plaid = false; }
      if ($in_plaid && preg_match('/^\s*access_token\s*=/', $line)) { $out[] = "access_token = $access"; $wrote = true; continue; }
      $out[] = $line;
    }
    if (!$wrote) { $out[] = "access_token = $access"; }
    file_put_contents($cfgPath, implode(PHP_EOL, $out).PHP_EOL);
    echo json_encode(["ok"=>true]); exit;
  }

  echo json_encode(["error"=>"unknown action"]);
} catch (Exception $e) {
  http_response_code(400);
  echo json_encode(["error"=>$e->getMessage()]);
}
