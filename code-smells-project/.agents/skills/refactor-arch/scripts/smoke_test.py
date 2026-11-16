#!/usr/bin/env python3
"""Smoke test genérico para a Fase 3 da skill refactor-arch.

Sobe a aplicação, chama uma lista de endpoints e registra (--out) ou compara
(--compare) status e formato do JSON com um baseline. Usa só a biblioteca
padrão, funciona com qualquer stack (Flask, Express, ...) em Windows, Linux e macOS.

Uso:
  python smoke_test.py --cmd "node src/app.js" --base-url http://localhost:3000 \
      --endpoints endpoints.json --out baseline.json
  python smoke_test.py --cmd "node src/app.js" --base-url http://localhost:3000 \
      --endpoints endpoints.json --compare baseline.json

Formato de endpoints.json: lista de objetos com
  name, method, path, [body], [headers], [expect_status], [capture]
  capture: {"variavel": "caminho.com.pontos"} guarda valores da resposta
  Use {variavel} em path e body para reutilizar.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def shape(value, depth=0):
    """Descreve o formato do JSON (chaves e tipos), ignorando os valores."""
    if depth > 6:
        return "..."
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0], depth + 1)] if value else []
    if value is None:
        return "null"
    return type(value).__name__


def get_path(data, path):
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def substitute(obj, variables):
    if isinstance(obj, str):
        return re.sub(r"\{(\w+)\}", lambda m: str(variables.get(m.group(1), m.group(0))), obj)
    if isinstance(obj, dict):
        return {k: substitute(v, variables) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(v, variables) for v in obj]
    return obj


def start_process(cmd, cwd, env, log_file):
    kwargs = dict(shell=True, cwd=cwd, env=env,
                  stdout=log_file, stderr=subprocess.STDOUT)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)


def stop_process(proc):
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def wait_for_server(base_url, proc, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False, "o processo terminou antes de abrir a porta"
        try:
            urllib.request.urlopen(base_url + "/", timeout=2)
            return True, ""
        except urllib.error.HTTPError:
            return True, ""  # respondeu (qualquer status): o servidor está de pé
        except Exception:
            time.sleep(0.4)
    return False, f"timeout de {timeout}s esperando {base_url}"


def call(base_url, ep, variables):
    method = ep.get("method", "GET").upper()
    path = substitute(ep["path"], variables)
    body = ep.get("body")
    headers = {"Accept": "application/json"}
    headers.update(ep.get("headers", {}))
    data = None
    if body is not None:
        data = json.dumps(substitute(body, variables)).encode()
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
        return status, parsed, shape(parsed)
    except ValueError:
        return status, text, "text"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", required=True, help="comando que inicia a aplicação")
    ap.add_argument("--base-url", required=True, help="ex.: http://localhost:5000")
    ap.add_argument("--endpoints", required=True, help="JSON com a lista de endpoints")
    ap.add_argument("--out", help="grava o baseline neste arquivo")
    ap.add_argument("--compare", help="compara com este baseline")
    ap.add_argument("--wait", type=int, default=30, help="segundos para a porta abrir")
    ap.add_argument("--cwd", default=".", help="diretório de execução (raiz do projeto)")
    ap.add_argument("--reset-file", action="append", default=[],
                    help="arquivo a apagar antes de subir (ex.: banco SQLite gerado). Repetível")
    ap.add_argument("--env", action="append", default=[], help="KEY=VALUE para a aplicação. Repetível")
    args = ap.parse_args()

    if not args.out and not args.compare:
        ap.error("informe --out (baseline) ou --compare")

    with open(args.endpoints, encoding="utf-8") as f:
        endpoints = json.load(f)
    baseline = None
    if args.compare:
        with open(args.compare, encoding="utf-8") as f:
            baseline = {r["name"]: r for r in json.load(f)}

    for path in args.reset_file:
        full = os.path.join(args.cwd, path)
        if os.path.exists(full):
            os.remove(full)
            print(f"[reset] apagado {full}")

    env = os.environ.copy()
    for kv in args.env:
        k, _, v = kv.partition("=")
        env[k] = v

    base_url = args.base_url.rstrip("/")
    log_file = tempfile.NamedTemporaryFile(prefix="refactor-arch-", suffix=".log", delete=False)
    proc = start_process(args.cmd, args.cwd, env, log_file)
    results, failures, diffs = [], 0, 0
    try:
        ok, why = wait_for_server(base_url, proc, args.wait)
        if not ok:
            stop_process(proc)
            log_file.flush()
            with open(log_file.name, encoding="utf-8", errors="replace") as lf:
                output = lf.read()
            print(f"FAIL  boot: a aplicação não subiu ({why})")
            if output:
                print("---- saída da aplicação ----")
                print(output[-3000:])
            return 1
        print(f"PASS  boot: servidor respondendo em {base_url}")

        variables = {}
        for ep in endpoints:
            name = ep["name"]
            label = f'{ep.get("method", "GET").upper():6} {ep["path"]}'
            try:
                status, parsed, shp = call(base_url, ep, variables)
            except Exception as e:  # erro de conexão, timeout...
                print(f"FAIL  {name} [{label}] erro de requisição: {e}")
                failures += 1
                results.append({"name": name, "status": None, "shape": None})
                continue

            for var, path in ep.get("capture", {}).items():
                try:
                    variables[var] = get_path(parsed, path)
                except Exception:
                    print(f"WARN  {name}: não foi possível capturar '{path}'")

            results.append({"name": name, "status": status, "shape": shp})
            expected = ep.get("expect_status")
            line = f"{name} [{label}] -> {status}"

            if baseline is not None:
                base = baseline.get(name)
                if base is None:
                    print(f"WARN  {line} (sem baseline para este endpoint)")
                elif base["status"] != status:
                    print(f"FAIL  {line} (baseline: {base['status']})")
                    failures += 1
                elif base["shape"] != shp:
                    print(f"DIFF  {line} (formato do JSON mudou)")
                    print(f"        antes : {json.dumps(base['shape'], ensure_ascii=False)}")
                    print(f"        depois: {json.dumps(shp, ensure_ascii=False)}")
                    diffs += 1
                else:
                    print(f"PASS  {line}")
            else:
                if expected is not None and expected != status:
                    print(f"FAIL  {line} (esperado {expected})")
                    failures += 1
                else:
                    print(f"OK    {line}")
    finally:
        stop_process(proc)
        try:
            log_file.close()
            os.remove(log_file.name)
        except OSError:
            pass

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nBaseline gravado em {args.out} ({len(results)} endpoints)")

    total = len(results)
    print(f"\nResumo: {total} endpoints | FAIL: {failures} | DIFF: {diffs}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
