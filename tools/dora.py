"""Calcula as métricas DORA do repositório a partir da API do GitHub (via `gh api`).

Uso: python tools/dora.py [owner/repo]

- Frequência de deploy: jobs de produção bem-sucedidos do workflow CD na main.
- Lead time: do commit (autoria) até o deploy em produção que o levou ao ar.
- Taxa de falha: deploys de produção seguidos de um rollback antes do próximo deploy.
- Tempo de restauração: duração dos runs do workflow Rollback em produção.
"""

import json
import statistics
import subprocess
import sys
from datetime import UTC, datetime, timedelta

REPO = sys.argv[1] if len(sys.argv) > 1 else "LuisEdu-dev/cafe-com-deploy-luisedu"


def gh(caminho: str):
    saida = subprocess.run(
        ["gh", "api", f"repos/{REPO}/{caminho}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return json.loads(saida)


def data(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def fmt(delta: timedelta) -> str:
    segundos = int(delta.total_seconds())
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}min"
    return f"{minutos}min{segundos:02d}s"


def jobs_de_producao(workflow: str) -> list[dict]:
    """Jobs de deploy em produção concluídos com sucesso, em ordem cronológica."""
    runs = gh(f"actions/workflows/{workflow}/runs?branch=main&per_page=100")["workflow_runs"]
    encontrados = []
    for run in runs:
        for job in gh(f"actions/runs/{run['id']}/jobs")["jobs"]:
            if "(production)" in job["name"] and job["conclusion"] == "success":
                encontrados.append(
                    {
                        "run": run["id"],
                        "sha": run["head_sha"],
                        "inicio": data(run["created_at"]),
                        "fim": data(job["completed_at"]),
                    }
                )
    return sorted(encontrados, key=lambda d: d["fim"])


def commits_do_deploy(sha_anterior: str | None, sha: str) -> list[dict]:
    if sha_anterior is None:
        commits = gh(f"commits?sha={sha}&per_page=100")
    elif sha_anterior == sha:
        return []
    else:
        commits = gh(f"compare/{sha_anterior}...{sha}")["commits"]
    return [c for c in commits if len(c["parents"]) == 1]  # ignora merges


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    deploys = jobs_de_producao("cd.yml")
    rollbacks = jobs_de_producao("rollback.yml")

    lead_times = []
    anterior = None
    for deploy in deploys:
        for commit in commits_do_deploy(anterior, deploy["sha"]):
            lead_times.append(deploy["fim"] - data(commit["commit"]["author"]["date"]))
        anterior = deploy["sha"]

    falhas = 0
    fim_dos_tempos = datetime.max.replace(tzinfo=UTC)
    for i, deploy in enumerate(deploys):
        proximo = deploys[i + 1]["fim"] if i + 1 < len(deploys) else fim_dos_tempos
        if any(deploy["fim"] < r["inicio"] < proximo for r in rollbacks):
            falhas += 1

    periodo = deploys[-1]["fim"] - deploys[0]["fim"] if len(deploys) > 1 else timedelta(0)
    dias = max(periodo.total_seconds() / 86400, 1)
    restauracoes = [r["fim"] - r["inicio"] for r in rollbacks]

    print("| Métrica | Valor |")
    print("|---|---|")
    print(
        f"| Frequência de deploy | {len(deploys)} deploys em produção "
        f"({len(deploys) / dias:.1f}/dia) |"
    )
    if lead_times:
        media = sum(lead_times, timedelta(0)) / len(lead_times)
        print(
            f"| Lead time para mudanças | média {fmt(media)}, "
            f"mediana {fmt(statistics.median(lead_times))} "
            f"({len(lead_times)} commits; mín. {fmt(min(lead_times))}, "
            f"máx. {fmt(max(lead_times))}) |"
        )
    if deploys:
        print(
            f"| Taxa de falha de mudança | {falhas}/{len(deploys)} "
            f"({100 * falhas / len(deploys):.0f}%) |"
        )
    if restauracoes:
        print(
            f"| Tempo de restauração (rollback) | mediana {fmt(statistics.median(restauracoes))} "
            f"({len(restauracoes)} runs do workflow Rollback) |"
        )


if __name__ == "__main__":
    main()
