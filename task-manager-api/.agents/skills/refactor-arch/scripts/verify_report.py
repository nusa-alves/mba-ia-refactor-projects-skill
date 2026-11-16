#!/usr/bin/env python3
"""Verifica o rascunho do relatório de auditoria contra o código real (Fase 2).

Somente leitura. Usa só a biblioteca padrão. Nunca altera arquivos do projeto.

Uso (o rascunho pode vir de um arquivo ou da entrada padrão):
  python verify_report.py --root . --report <rascunho.md>
  python verify_report.py --root . --report -          # lê da entrada padrão
  python verify_report.py <rascunho.md> --root .       # forma posicional

O que confere:
  - cada "arquivo:linha" ou "arquivo:ini-fim" existe e está dentro do arquivo;
  - linhas citadas em branco, e intervalos que começam ou terminam em branco;
  - evidência: o trecho citado combina com o título do finding
    (SQL Injection precisa de concatenação/interpolação; "Logging por print"
    precisa de print/console.log; "Imports sem uso" só vale para nomes
    realmente sem uso no arquivo);
  - Summary e Total batem com os findings; ordem CRITICAL -> LOW;
  - cobertura: sinais no código (God File, CORS aberto, APIs deprecated,
    segredo hardcoded, SQL concatenado, estado global...) sem finding
    correspondente viram WARN.

Saída: ERROR (corrija ou remova a citação), WARN (confira), OK.
Código de saída 1 se houver ERROR.
"""
import argparse
import os
import re
import sys

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
WIDE_RANGE = 40          # acima disso: aviso de intervalo largo
EVIDENCE_MAX_RANGE = 12  # evidência só é exigida em citações curtas
GOD_FILE_LINES = 250     # arquivo com mais linhas que isso é candidato a God File

SOURCE_EXT = (".py", ".js", ".mjs", ".cjs", ".ts", ".java", ".php", ".rb", ".go", ".cs")
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "env", "__pycache__", ".agents", ".claude",
             "dist", "build", "reports", ".idea", ".vscode", "site-packages", "vendor", "coverage"}

# Evidência esperada por título (o PRIMEIRO padrão de título que casar vale; a ordem importa).
EVIDENCE = [
    (r"sem autentica|endpoints? sens|destrutiv",
     r"route|def\s|app\.(get|post|put|delete|patch)|router\.|admin|delete|drop|reset"),
    (r"credencia|segredo|hardcoded|secret",
     r"secret|passw|senha|token|api_?key|smtp|debug|pk_|sk_|chave"),
    (r"exposi|sens.ve",
     r"senha|passw|secret|db_path|debug|str\(\s*e\s*\)|\bpass\b|card|hash|\.stack|err\.message"),
    (r"senha|password|armazenamento",
     r"senha|passw|\bpass\b|md5|sha1|hash|crypt|token|role|login"),
    (r"n\+1", r"execute\(|\.query|\.get\(|\.all\(|\.run\(|\.find|for\s+\w+\s+in|forEach|\.map\("),
    (r"transa", r"execute\(|commit|insert|update|delete|\.run\(|rollback"),
    (r"tratamento de erro|erro", r"except|catch|str\(\s*e\s*\)|err\b|error|\.status\(5"),
    (r"cors", r"cors|access-control"),
]

# Cobertura: chave -> regex de título que "cobre" o sinal
COVER = {
    "god": r"god|monol",
    "cors": r"cors",
    "deprecated": r"deprecat|obsolet",
    "secrets": r"credencia|segredo|hardcoded|secret",
    "sqli": r"sql",
    "global": r"global",
    "logging": r"logging|print|console",
    "errors": r"erro|error|except|tratamento",
    "n1": r"n\+1",
    "admin": r"sem autentica|endpoints? sens|destrutiv|admin",
}

COVER_NAMES = {
    "god": "God File/Class (arquivo grande que mistura camadas ou domínios)",
    "cors": "CORS aberto",
    "deprecated": "API deprecated/obsoleta",
    "secrets": "credencial ou segredo hardcoded",
    "sqli": "SQL montado por concatenação/interpolação",
    "global": "estado global mutável",
    "logging": "logging por print/console.log",
    "errors": "tratamento de erro genérico/repetido",
    "n1": "consulta dentro de loop (N+1)",
    "admin": "rota administrativa/destrutiva",
}


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def parse_report(text):
    findings, cur = [], None
    summary, total = None, None
    for raw in text.split("\n"):
        line = raw.rstrip()
        m = re.match(r"^#{2,4}\s*\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s*(.+)$", line.strip())
        if m:
            cur = {"sev": m.group(1), "title": m.group(2).strip(), "file": "", "desc": ""}
            findings.append(cur)
            continue
        ms = re.search(r"CRITICAL:\s*(\d+)\s*\|\s*HIGH:\s*(\d+)\s*\|\s*MEDIUM:\s*(\d+)\s*\|\s*LOW:\s*(\d+)", line)
        if ms:
            summary = dict(zip(SEVERITIES, map(int, ms.groups())))
        mt = re.match(r"^\s*Total:\s*(\d+)\s+findings?", line)
        if mt:
            total = int(mt.group(1))
            cur = None
        if cur is not None:
            if line.startswith("File:"):
                cur["file"] = line[len("File:"):].strip()
            elif line.startswith("Description:"):
                cur["desc"] = line[len("Description:"):].strip()
    return findings, summary, total


def parse_cites(file_field):
    """'a.py:1-3, b.py:5, 9-12' -> [(arquivo, ini, fim), ...] (números soltos herdam o arquivo anterior)."""
    cites, last = [], None
    for part in [p.strip() for p in file_field.split(",") if p.strip()]:
        m = re.match(r"^(.+?):(\d+)(?:\s*-\s*(\d+))?$", part)
        if m:
            last = m.group(1).strip().strip("`")
            ini = int(m.group(2))
            fim = int(m.group(3)) if m.group(3) else ini
            cites.append((last, ini, fim))
            continue
        m = re.match(r"^(\d+)(?:\s*-\s*(\d+))?$", part)
        if m and last:
            ini = int(m.group(1))
            fim = int(m.group(2)) if m.group(2) else ini
            cites.append((last, ini, fim))
            continue
        cites.append((part, None, None))
    return cites


def import_names(line):
    """Nomes importados em uma linha de import (Python ou JS)."""
    s = line.strip()
    names = []
    m = re.match(r"^from\s+[\w.]+\s+import\s+(.+)$", s)
    if m:
        for p in m.group(1).strip("()").split(","):
            p = p.strip()
            if p and p != "*":
                names.append(p.split(" as ")[-1].strip())
        return names
    m = re.match(r"^import\s+(.+)$", s)
    if m and not re.search(r"\bfrom\b", s):
        for p in m.group(1).split(","):
            p = p.strip()
            if p:
                names.append(p.split(" as ")[-1].strip().split(".")[0])
        return names
    m = re.match(r"^(?:const|let|var)\s+\{([^}]*)\}\s*=\s*require\(", s)
    if m:
        for p in m.group(1).split(","):
            p = p.strip()
            if p:
                names.append(p.split(":")[-1].strip())
        return names
    m = re.match(r"^(?:const|let|var)\s+(\w+)\s*=\s*require\(", s)
    if m:
        return [m.group(1)]
    m = re.match(r"^import\s+(?:(\w+)\s*,?\s*)?(?:\{([^}]*)\})?\s*(?:\*\s+as\s+(\w+))?\s*from\s+", s)
    if m:
        if m.group(1):
            names.append(m.group(1))
        if m.group(2):
            names += [p.split(" as ")[-1].strip() for p in m.group(2).split(",") if p.strip()]
        if m.group(3):
            names.append(m.group(3))
        return names
    return []


def source_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(SOURCE_EXT):
                out.append(os.path.join(d, f))
    return out


def coverage_signals(root):
    """Procura sinais de anti-patterns no código. Devolve {chave: [(arquivo, linha, texto)]}."""
    sig = {k: [] for k in COVER}
    n_print, n_except = [], []
    for path in source_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        lines = read_lines(path)
        if len(lines) > GOD_FILE_LINES:
            sig["god"].append((rel, 1, f"{len(lines)} linhas"))
        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            if s.startswith(("#", "//", "*")):
                continue
            if re.search(r"\bCORS\(\s*\w+\s*\)|\bcors\(\s*\)", ln):
                sig["cors"].append((rel, i, s))
            if re.search(r"utcnow\(|utcfromtimestamp\(|\.query\.get\(|new Buffer\(|bodyParser|body-parser|"
                         r"\bfs\.exists\(|logging\.warn\(|createCipher\(|\bimport imp\b|\bdistutils\b", ln):
                sig["deprecated"].append((rel, i, s))
            if re.search(r"(?i)(secret_key|secret|passw(or)?d|senha|api_?key|token|smtp_?pass\w*)[\w]*[\"']?\s*[:=]\s*[\"'][^\"']{4,}[\"']", ln) \
                    and not re.search(r"environ|getenv|process\.env|\.get\(", ln):
                sig["secrets"].append((rel, i, s))
            if re.search(r"(?i)\b(select|insert|update|delete)\b", ln) and \
                    re.search(r"[\"']\s*\+|\+\s*[\"']|\+\s*str\(|\bf[\"']|\$\{|\.format\(", ln):
                sig["sqli"].append((rel, i, s))
            if re.match(r"^\s*global\s+\w+", ln):
                sig["global"].append((rel, i, s))
            if re.search(r"\bprint\(|console\.(log|error|warn|info)\(", ln):
                n_print.append((rel, i, s))
            if re.search(r"except\s*:|except\s+Exception|catch\s*\(", ln):
                n_except.append((rel, i, s))
            if re.search(r"/admin|reset-db|reset_db", ln):
                sig["admin"].append((rel, i, s))
            if re.match(r"^\s*for\s+.+\s+in\s+.+:\s*$", ln) or re.search(r"\.forEach\(", ln):
                window = lines[i:i + 8]
                if any(re.search(r"execute\(|\.query\.get\(|\bdb\.(get|all|run)\(|this\.db\.(get|all|run)\(", w) for w in window):
                    sig["n1"].append((rel, i, s))
    if len(n_print) >= 3:
        sig["logging"] = n_print
    if len(n_except) >= 3:
        sig["errors"] = n_except
    return sig


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_pos", nargs="?", help="rascunho do relatório (forma posicional)")
    ap.add_argument("--report", help="rascunho do relatório; use '-' para ler da entrada padrão")
    ap.add_argument("--root", default=".", help="raiz do projeto (para resolver os caminhos)")
    ap.add_argument("--verbose", action="store_true", help="mostra também as citações sem problema")
    ap.add_argument("--no-coverage", action="store_true", help="não procura sinais sem finding")
    args = ap.parse_args()

    src = args.report or args.report_pos
    if not src:
        ap.error("informe o rascunho: --report <arquivo> ou --report - (entrada padrão)")
    if src == "-":
        text = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    else:
        with open(src, encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    findings, summary, total = parse_report(text)

    counts = {"ERROR": 0, "WARN": 0}
    cache = {}

    def file_lines(rel):
        rel = rel.replace("\\", "/")
        if rel not in cache:
            p = os.path.join(args.root, rel)
            cache[rel] = read_lines(p) if os.path.isfile(p) else None
        return cache[rel]

    def report(level, msg):
        counts[level] += 1
        print(f"  {level:5} {msg}")

    if not findings:
        print("ERROR nenhum finding encontrado. Formato esperado: '### [SEVERIDADE] Título'.")
        return 1

    for idx, fd in enumerate(findings, 1):
        print(f"#{idx} [{fd['sev']}] {fd['title']}")
        before = counts["ERROR"] + counts["WARN"]
        cites = parse_cites(fd["file"]) if fd["file"] else []
        if not cites:
            report("ERROR", "campo 'File:' ausente ou vazio")
            continue

        evidence_re = None
        for tre, ere in EVIDENCE:
            if re.search(tre, fd["title"], re.I):
                evidence_re = re.compile(ere, re.I)
                break
        is_sqli = re.search(r"sql injection|inje.{1,3}o de sql", fd["title"], re.I) is not None
        is_print = re.search(r"logging|print|console", fd["title"], re.I) is not None
        is_unused = re.search(r"sem uso|unused|n.o utilizad", fd["title"], re.I) is not None

        for rel, ini, fim in cites:
            label = (f"{rel}:{ini}" + (f"-{fim}" if fim != ini else "")) if ini else rel
            if ini is None:
                report("ERROR", f"{label}: citação não reconhecida (use arquivo:linha ou arquivo:ini-fim)")
                continue
            lines = file_lines(rel)
            if lines is None:
                report("ERROR", f"{label}: arquivo não encontrado a partir de {os.path.abspath(args.root)}")
                continue
            total_lines = len(lines) - (1 if lines and lines[-1] == "" else 0)
            if ini < 1 or fim < ini or fim > total_lines:
                report("ERROR", f"{label}: fora do arquivo (o arquivo tem {total_lines} linhas)")
                continue

            chunk = lines[ini - 1:fim]
            flagged = False

            if ini == fim and not chunk[0].strip():
                report("ERROR", f"{label}: linha em branco")
                flagged = True
            elif not chunk[0].strip() or not chunk[-1].strip():
                report("WARN", f"{label}: o intervalo começa ou termina em linha em branco (aperte o intervalo)")
                flagged = True
            if fim - ini + 1 > WIDE_RANGE:
                report("WARN", f"{label}: intervalo largo ({fim - ini + 1} linhas). Cite só as linhas do problema, "
                               f"a menos que o problema seja o arquivo todo")
                flagged = True

            joined = "\n".join(chunk)

            if is_sqli:
                has_dyn = re.search(r"\+|f[\"']|\$\{|\.format\(|%\s*\(|%s[^\n]*%\s*\w", joined)
                if not has_dyn:
                    if re.search(r"execute\(\s*\w+\s*\)|\.(all|get|run)\(\s*\w+\s*[,)]", joined):
                        report("WARN", f"{label}: execute com variável; confirme de onde vem a string "
                                       f"(requisição? concatenação em outra linha?)")
                    else:
                        report("ERROR", f"{label}: sem concatenação ou interpolação (consulta fixa não é SQL Injection)")
                    flagged = True
            elif is_print:
                if not re.search(r"\bprint\(|console\.(log|error|warn|info)\(", joined):
                    report("ERROR", f"{label}: nenhuma linha tem print() ou console.*")
                    flagged = True
            elif is_unused:
                names_found = []
                for k, ln in enumerate(chunk):
                    names_found += [(n, ini + k) for n in import_names(ln)]
                if not names_found:
                    report("WARN", f"{label}: não é uma linha de import reconhecida; "
                                   f"confirme com busca do nome no arquivo")
                    flagged = True
                else:
                    mentioned = [(n, l) for n, l in names_found if re.search(rf"\b{re.escape(n)}\b", fd["desc"])]
                    for name, _ in (mentioned or names_found):
                        uses = [j for j, l in enumerate(lines, 1)
                                if not (ini <= j <= fim) and re.search(rf"\b{re.escape(name)}\b", l)]
                        if uses:
                            report("ERROR", f"{label}: '{name}' está em uso (por exemplo, {rel}:{uses[0]}). "
                                            f"Não é import sem uso")
                            flagged = True
            elif evidence_re is not None and (fim - ini + 1) <= EVIDENCE_MAX_RANGE:
                if not evidence_re.search(joined):
                    report("ERROR", f"{label}: o trecho citado não mostra o problema descrito no título")
                    flagged = True

            if args.verbose and not flagged:
                print(f"  OK    {label}")
            if args.verbose or flagged:
                shown = chunk if len(chunk) <= 4 else chunk[:2] + ["..."] + chunk[-1:]
                nums = list(range(ini, fim + 1))
                nums = nums if len(chunk) <= 4 else nums[:2] + [None] + nums[-1:]
                for n, l in zip(nums, shown):
                    print(f"          {'' if n is None else n:>5}| {l[:100]}")

        if counts["ERROR"] + counts["WARN"] == before:
            print("  OK    todas as citações conferem")

    print("\n== Contagens ==")
    actual = {s: sum(1 for f in findings if f["sev"] == s) for s in SEVERITIES}
    if summary is None:
        report("ERROR", "linha 'Summary' (CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n) não encontrada")
    elif summary != actual:
        report("ERROR", f"Summary diz {summary}, mas o relatório tem {actual}")
    else:
        print(f"  OK    Summary confere: {actual}")
    if total is None:
        report("ERROR", "linha 'Total: N findings' não encontrada")
    elif total != len(findings):
        report("ERROR", f"Total diz {total}, mas o relatório tem {len(findings)} findings")
    else:
        print(f"  OK    Total confere: {total}")
    order = [SEVERITIES.index(f["sev"]) for f in findings]
    if order != sorted(order):
        report("ERROR", "findings fora de ordem (esperado CRITICAL, HIGH, MEDIUM, LOW)")
    else:
        print("  OK    ordem CRITICAL -> LOW")

    if not args.no_coverage:
        print("\n== Cobertura (sinais no código sem finding correspondente) ==")
        sig = coverage_signals(args.root)
        titles = [f["title"] for f in findings]
        missing = 0
        for key, hits in sig.items():
            if not hits:
                continue
            if any(re.search(COVER[key], t, re.I) for t in titles):
                continue
            missing += 1
            report("WARN", f"há sinal de '{COVER_NAMES[key]}' no código e nenhum finding com esse tema")
            for rel, ln, txt in hits[:3]:
                print(f"          {rel}:{ln}| {txt[:90]}")
            if len(hits) > 3:
                print(f"          ... e mais {len(hits) - 3} ocorrência(s)")
        if not missing:
            print("  OK    todo sinal encontrado tem finding correspondente")
        else:
            print("  (WARN de cobertura: registre o finding ou confirme por que não se aplica.)")

    print(f"\nResumo: {len(findings)} findings | ERROR: {counts['ERROR']} | WARN: {counts['WARN']}")
    if counts["ERROR"]:
        print("Corrija ou remova as citações com ERROR, atualize o rascunho e rode de novo.")
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
