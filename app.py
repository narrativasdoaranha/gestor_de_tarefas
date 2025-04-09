import streamlit as st
import pandas as pd
import datetime
import json
import os

# Configuração da página
st.set_page_config(page_title="Gestor de Tarefas", layout="wide")

# Função para carregar dados
def carregar_dados():
    # Verificar se os arquivos existem
    if not os.path.exists("tarefas_recorrentes.json"):
        with open("tarefas_recorrentes.json", "w") as f:
            json.dump([], f)
    
    if not os.path.exists("backlog.json"):
        with open("backlog.json", "w") as f:
            json.dump([], f)
    
    if not os.path.exists("historico.json"):
        with open("historico.json", "w") as f:
            json.dump({}, f)
    
    if not os.path.exists("tarefas_dia.json"):
        with open("tarefas_dia.json", "w") as f:
            json.dump({"data": "", "tarefas": []}, f)
    
    if not os.path.exists("projetos.json"):
        with open("projetos.json", "w") as f:
            json.dump([], f)
    
    # Carregar dados
    with open("tarefas_recorrentes.json", "r") as f:
        tarefas_recorrentes = json.load(f)
    
    with open("backlog.json", "r") as f:
        backlog = json.load(f)
    
    with open("historico.json", "r") as f:
        historico = json.load(f)
    
    with open("tarefas_dia.json", "r") as f:
        tarefas_dia = json.load(f)
    
    with open("projetos.json", "r") as f:
        projetos = json.load(f)
    
    # Converter histórico antigo para o novo formato se necessário
    historico_atualizado = {}
    for tarefa_id, dados in historico.items():
        if isinstance(dados, list):  # Formato muito antigo (só datas)
            sequencia = calcular_sequencia_antiga(dados)
            historico_atualizado[tarefa_id] = {
                "datas": dados,
                "sequencia_atual": sequencia,
                "sequencia_editada": False,
                "recorde_sequencia": sequencia
            }
        elif isinstance(dados, dict) and "recorde_sequencia" not in dados:  # Formato antigo sem recorde
            dados["recorde_sequencia"] = dados.get("sequencia_atual", 0)
            historico_atualizado[tarefa_id] = dados
        else:  # Já está no formato novo
            historico_atualizado[tarefa_id] = dados
    
    return tarefas_recorrentes, backlog, historico_atualizado, tarefas_dia, projetos

# Função auxiliar para calcular sequência no formato antigo
def calcular_sequencia_antiga(datas):
    if not datas:
        return 0
    
    datas_obj = [datetime.datetime.strptime(data, "%Y-%m-%d") for data in datas]
    datas_obj.sort()
    
    data_atual = datetime.datetime.now().date()
    ultima_data = datas_obj[-1].date()
    
    # Se a última conclusão não foi hoje nem ontem, a sequência foi quebrada
    if (data_atual - ultima_data).days > 1:
        return 0
    
    # Calcular sequência atual
    sequencia = 1
    for i in range(len(datas_obj) - 1, 0, -1):
        dias_diff = (datas_obj[i].date() - datas_obj[i-1].date()).days
        if dias_diff == 1:
            sequencia += 1
        else:
            break
    
    return sequencia

# Função para salvar dados
def salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos):
    with open("tarefas_recorrentes.json", "w") as f:
        json.dump(tarefas_recorrentes, f)
    
    with open("backlog.json", "w") as f:
        json.dump(backlog, f)
    
    with open("historico.json", "w") as f:
        json.dump(historico, f)
    
    with open("tarefas_dia.json", "w") as f:
        json.dump(tarefas_dia, f)
    
    with open("projetos.json", "w") as f:
        json.dump(projetos, f)

# Função para calcular sequência atual
def calcular_sequencia(historico, tarefa_id):
    if tarefa_id not in historico:
        return 0
    
    info_tarefa = historico[tarefa_id]
    
    # Se a sequência foi editada manualmente, usar esse valor
    if info_tarefa.get("sequencia_editada", False):
        return info_tarefa.get("sequencia_atual", 0)
    
    # Caso contrário, calcular com base nas datas
    datas = info_tarefa.get("datas", [])
    if not datas:
        return 0
    
    datas_obj = [datetime.datetime.strptime(data, "%Y-%m-%d") for data in datas]
    datas_obj.sort()
    
    data_atual = datetime.datetime.now().date()
    ultima_data = datas_obj[-1].date()
    
    # Se a última conclusão não foi hoje nem ontem, a sequência foi quebrada
    if (data_atual - ultima_data).days > 1:
        return 0
    
    # Calcular sequência atual
    sequencia = 1
    for i in range(len(datas_obj) - 1, 0, -1):
        dias_diff = (datas_obj[i].date() - datas_obj[i-1].date()).days
        if dias_diff == 1:
            sequencia += 1
        else:
            break
    
    return sequencia

# Função para atualizar o recorde de sequência
def atualizar_recorde(historico, tarefa_id):
    if tarefa_id not in historico:
        return
    
    sequencia_atual = historico[tarefa_id].get("sequencia_atual", 0)
    recorde_atual = historico[tarefa_id].get("recorde_sequencia", 0)
    
    if sequencia_atual > recorde_atual:
        historico[tarefa_id]["recorde_sequencia"] = sequencia_atual

# Função principal
def main():
    st.title("Gestor de Tarefas")
    
    # Carregar dados
    tarefas_recorrentes, backlog, historico, tarefas_dia, projetos = carregar_dados()
    
    # Data atual
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Se for um novo dia, resetar as tarefas do dia
    if tarefas_dia["data"] != hoje:
        tarefas_dia = {
            "data": hoje,
            "tarefas": [{"id": tarefa["id"], "descricao": tarefa["descricao"], "tipo": "recorrente", "concluida": False} 
                       for tarefa in tarefas_recorrentes]
        }
        salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
    
    # Sidebar com abas
    with st.sidebar:
        aba = st.radio("Menu", ["Tarefas do Dia", "Tarefas Recorrentes", "Backlog", "Projetos", "Estatísticas", "Editar Sequências"])
    
    # Aba de tarefas do dia
    if aba == "Tarefas do Dia":
        st.header(f"Tarefas do Dia ({hoje})")
        
        # Mostrar tarefas do dia
        if not tarefas_dia["tarefas"]:
            st.info("Não há tarefas para hoje. Adicione tarefas recorrentes ou selecione do backlog.")
        
        for i, tarefa in enumerate(tarefas_dia["tarefas"]):
            col1, col2, col3, col4 = st.columns([0.1, 1.6, 0.2, 0.1])
            with col1:
                concluida = st.checkbox("", tarefa["concluida"], key=f"tarefa_dia_{i}")
                if concluida != tarefa["concluida"]:
                    tarefa["concluida"] = concluida
                    
                    # Atualizar histórico se marcou como concluída
                    if concluida and tarefa["tipo"] == "recorrente":
                        if tarefa["id"] not in historico:
                            historico[tarefa["id"]] = {
                                "datas": [],
                                "sequencia_atual": 0,
                                "sequencia_editada": False,
                                "recorde_sequencia": 0
                            }
                        
                        if hoje not in historico[tarefa["id"]]["datas"]:
                            historico[tarefa["id"]]["datas"].append(hoje)
                            # Recalcular a sequência
                            if not historico[tarefa["id"]]["sequencia_editada"]:
                                historico[tarefa["id"]]["sequencia_atual"] = calcular_sequencia(historico, tarefa["id"])
                            else:
                                # Se editada manualmente, incrementar
                                historico[tarefa["id"]]["sequencia_atual"] += 1
                            
                            # Atualizar recorde se necessário
                            atualizar_recorde(historico, tarefa["id"])
                    
                    # Remover do histórico se desmarcou
                    elif not concluida and tarefa["tipo"] == "recorrente":
                        if tarefa["id"] in historico and hoje in historico[tarefa["id"]]["datas"]:
                            historico[tarefa["id"]]["datas"].remove(hoje)
                            # Recalcular a sequência
                            if not historico[tarefa["id"]]["sequencia_editada"]:
                                historico[tarefa["id"]]["sequencia_atual"] = calcular_sequencia(historico, tarefa["id"])
                            else:
                                # Se editada manualmente, decrementar (mas não abaixo de 0)
                                historico[tarefa["id"]]["sequencia_atual"] = max(0, historico[tarefa["id"]]["sequencia_atual"] - 1)
                    
                    salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
            
            with col2:
                st.write(f"**{tarefa['descricao']}**" if not concluida else f"~~{tarefa['descricao']}~~")
            
            with col3:
                # Mostrar projeto se for tarefa do backlog
                if tarefa["tipo"] == "backlog":
                    backlog_task = next((t for t in backlog if t["id"] == tarefa["id"]), None)
                    if backlog_task and "projeto" in backlog_task:
                        st.write(f"📂 {backlog_task['projeto']}")
            
            with col4:
                tipo_tag = "🔄" if tarefa["tipo"] == "recorrente" else "📋"
                st.write(tipo_tag)
        
        # Adicionar tarefas do backlog
        st.subheader("Adicionar tarefas do backlog")
        
        if not backlog:
            st.info("Não há tarefas no backlog.")
        else:
            tarefas_disponiveis = [t for t in backlog if t["id"] not in [task["id"] for task in tarefas_dia["tarefas"]]]
            
            if not tarefas_disponiveis:
                st.info("Todas as tarefas do backlog já foram adicionadas ao dia.")
            else:
                # Filtro por projeto
                if projetos:
                    projeto_filtro = st.selectbox(
                        "Filtrar por projeto:",
                        ["Todos"] + [p["nome"] for p in projetos]
                    )
                
                    if projeto_filtro != "Todos":
                        tarefas_disponiveis = [t for t in tarefas_disponiveis if t.get("projeto") == projeto_filtro]
                
                selected_backlog = st.multiselect(
                    "Selecione tarefas do backlog para adicionar ao dia:",
                    options=[t["descricao"] for t in tarefas_disponiveis],
                    format_func=lambda x: x
                )
                
                if st.button("Adicionar Selecionadas"):
                    for descricao in selected_backlog:
                        tarefa = next((t for t in tarefas_disponiveis if t["descricao"] == descricao), None)
                        if tarefa:
                            tarefas_dia["tarefas"].append({
                                "id": tarefa["id"],
                                "descricao": tarefa["descricao"],
                                "tipo": "backlog",
                                "concluida": False
                            })
                    
                    salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                    st.rerun()
    
    # Aba de tarefas recorrentes
    elif aba == "Tarefas Recorrentes":
        st.header("Tarefas Recorrentes")
        
        # Formulário para adicionar nova tarefa recorrente
        with st.form(key="form_tarefa_recorrente"):
            nova_tarefa = st.text_input("Nova tarefa recorrente:")
            submit_button = st.form_submit_button("Adicionar")
            
            if submit_button and nova_tarefa:
                # Criar ID para a tarefa
                task_id = f"rec_{len(tarefas_recorrentes) + 1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Adicionar à lista de tarefas recorrentes
                tarefas_recorrentes.append({
                    "id": task_id,
                    "descricao": nova_tarefa
                })
                
                # Adicionar às tarefas do dia
                tarefas_dia["tarefas"].append({
                    "id": task_id,
                    "descricao": nova_tarefa,
                    "tipo": "recorrente",
                    "concluida": False
                })
                
                # Inicializar histórico desta tarefa
                historico[task_id] = {
                    "datas": [],
                    "sequencia_atual": 0,
                    "sequencia_editada": False,
                    "recorde_sequencia": 0
                }
                
                salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                st.rerun()
        
        # Listar tarefas recorrentes
        if not tarefas_recorrentes:
            st.info("Não há tarefas recorrentes cadastradas.")
        else:
            for i, tarefa in enumerate(tarefas_recorrentes):
                col1, col2, col3, col4 = st.columns([1.2, 0.3, 0.3, 0.2])
                
                with col1:
                    st.write(f"{i+1}. {tarefa['descricao']}")
                
                with col2:
                    # Mostrar sequência atual
                    seq = calcular_sequencia(historico, tarefa["id"])
                    st.write(f"Sequência: {seq} dias")
                
                with col3:
                    # Mostrar recorde de sequência
                    rec = historico.get(tarefa["id"], {}).get("recorde_sequencia", 0)
                    st.write(f"Recorde: {rec} dias")
                
                with col4:
                    # Total de vezes concluída
                    total = len(historico.get(tarefa["id"], {}).get("datas", []))
                    st.write(f"Total: {total}")
                
                if st.button("Remover", key=f"rem_rec_{i}"):
                    # Remover da lista de tarefas recorrentes
                    tarefas_recorrentes.pop(i)
                    
                    # Remover das tarefas do dia se estiver lá
                    tarefas_dia["tarefas"] = [t for t in tarefas_dia["tarefas"] if t["id"] != tarefa["id"]]
                    
                    salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                    st.rerun()
    
    # Aba de backlog
    elif aba == "Backlog":
        st.header("Backlog de Tarefas")
        
        # Formulário para adicionar nova tarefa ao backlog
        with st.form(key="form_backlog"):
            nova_tarefa = st.text_input("Nova tarefa para o backlog:")
            
            # Seleção de projeto
            projeto_options = ["Sem projeto"] + [p["nome"] for p in projetos]
            projeto_selecionado = st.selectbox("Projeto:", projeto_options)
            
            submit_button = st.form_submit_button("Adicionar")
            
            if submit_button and nova_tarefa:
                # Criar ID para a tarefa
                task_id = f"back_{len(backlog) + 1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Adicionar ao backlog
                tarefa_nova = {
                    "id": task_id,
                    "descricao": nova_tarefa
                }
                
                # Adicionar projeto se selecionado
                if projeto_selecionado != "Sem projeto":
                    tarefa_nova["projeto"] = projeto_selecionado
                
                backlog.append(tarefa_nova)
                
                salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                st.rerun()
        
        # Filtro de projeto para visualização
        if projetos:
            filtro_projeto = st.selectbox(
                "Filtrar por projeto:",
                ["Todos"] + [p["nome"] for p in projetos] + ["Sem projeto"],
                key="filtro_backlog"
            )
            
            if filtro_projeto != "Todos":
                if filtro_projeto == "Sem projeto":
                    backlog_filtrado = [t for t in backlog if "projeto" not in t]
                else:
                    backlog_filtrado = [t for t in backlog if t.get("projeto") == filtro_projeto]
            else:
                backlog_filtrado = backlog
        else:
            backlog_filtrado = backlog
        
        # Listar tarefas do backlog
        if not backlog_filtrado:
            st.info("Não há tarefas no backlog com este filtro.")
        else:
            for i, tarefa in enumerate(backlog_filtrado):
                col1, col2, col3 = st.columns([1.5, 0.3, 0.2])
                
                with col1:
                    st.write(f"{i+1}. {tarefa['descricao']}")
                
                with col2:
                    if "projeto" in tarefa:
                        st.write(f"📂 {tarefa['projeto']}")
                    else:
                        st.write("📂 Sem projeto")
                
                with col3:
                    if st.button("Remover", key=f"rem_back_{i}"):
                        # Encontrar o índice real no backlog completo
                        idx_real = next((j for j, t in enumerate(backlog) if t["id"] == tarefa["id"]), None)
                        if idx_real is not None:
                            # Remover do backlog
                            backlog.pop(idx_real)
                            
                            # Remover das tarefas do dia se estiver lá
                            tarefas_dia["tarefas"] = [t for t in tarefas_dia["tarefas"] if t["id"] != tarefa["id"]]
                            
                            salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                            st.rerun()
    
    # Aba de projetos
    elif aba == "Projetos":
        st.header("Gerenciar Projetos")
        
        # Formulário para adicionar novo projeto
        with st.form(key="form_projeto"):
            novo_projeto = st.text_input("Nome do novo projeto:")
            submit_button = st.form_submit_button("Adicionar Projeto")
            
            if submit_button and novo_projeto:
                # Verificar se já existe
                if not any(p["nome"] == novo_projeto for p in projetos):
                    # Adicionar à lista de projetos
                    projetos.append({
                        "id": f"proj_{len(projetos) + 1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "nome": novo_projeto
                    })
                    
                    salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                    st.rerun()
                else:
                    st.error("Já existe um projeto com este nome.")
        
        # Listar projetos
        if not projetos:
            st.info("Não há projetos cadastrados.")
        else:
            st.subheader("Projetos Existentes")
            for i, projeto in enumerate(projetos):
                col1, col2 = st.columns([1.8, 0.2])
                
                with col1:
                    st.write(f"{i+1}. {projeto['nome']}")
                
                with col2:
                    # Contagem de tarefas neste projeto
                    count = sum(1 for t in backlog if t.get("projeto") == projeto["nome"])
                    st.write(f"{count} tarefas")
                
                if st.button("Remover", key=f"rem_proj_{i}"):
                    # Remover projeto e atualizar tarefas
                    for tarefa in backlog:
                        if tarefa.get("projeto") == projeto["nome"]:
                            tarefa.pop("projeto", None)
                    
                    projetos.pop(i)
                    salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                    st.rerun()
    
    # Aba de estatísticas
    elif aba == "Estatísticas":
        st.header("Estatísticas")
        
        # Estatísticas gerais
        col1, col2 = st.columns(2)
        
        with col1:
            # Total de tarefas no backlog
            total_backlog = len(backlog)
            st.metric(label="Tarefas no Backlog", value=total_backlog)
            
            # Tarefas no backlog por projeto
            if projetos:
                st.subheader("Tarefas por Projeto")
                dados_projetos = []
                for projeto in projetos:
                    count = sum(1 for t in backlog if t.get("projeto") == projeto["nome"])
                    dados_projetos.append({"Projeto": projeto["nome"], "Tarefas": count})
                
                # Adicionar "Sem projeto"
                count_sem_projeto = sum(1 for t in backlog if "projeto" not in t)
                dados_projetos.append({"Projeto": "Sem projeto", "Tarefas": count_sem_projeto})
                
                df_projetos = pd.DataFrame(dados_projetos)
                st.dataframe(df_projetos, use_container_width=True)
        
        with col2:
            # Total geral de conclusões
            total_geral = sum(len(info.get("datas", [])) for info in historico.values())
            st.metric(label="Total de Tarefas Concluídas", value=total_geral)
            
            # Tarefas concluídas hoje
            tarefas_hoje = sum(1 for t in tarefas_dia["tarefas"] if t["concluida"])
            total_tarefas_hoje = len(tarefas_dia["tarefas"])
            st.metric(
                label="Tarefas Concluídas Hoje",
                value=f"{tarefas_hoje}/{total_tarefas_hoje}",
                delta=f"{int(tarefas_hoje/total_tarefas_hoje*100)}%" if total_tarefas_hoje > 0 else "0%"
            )
        
        # Estatísticas das tarefas recorrentes
        if tarefas_recorrentes:
            st.subheader("Desempenho de Tarefas Recorrentes")
            
            # Tabela simplificada com os dados solicitados
            dados_stats = []
            for tarefa in tarefas_recorrentes:
                info_tarefa = historico.get(tarefa["id"], {})
                total = len(info_tarefa.get("datas", []))
                sequencia = info_tarefa.get("sequencia_atual", 0)
                recorde = info_tarefa.get("recorde_sequencia", 0)
                
                dados_stats.append({
                    "Tarefa": tarefa["descricao"],
                    "Total de Dias": total,
                    "Dias Consecutivos": sequencia,
                    "Recorde de Dias Consecutivos": recorde
                })
            
            if dados_stats:
                df_stats = pd.DataFrame(dados_stats)
                st.dataframe(df_stats, use_container_width=True)
    
    # Aba para editar sequências
    elif aba == "Editar Sequências":
        st.header("Editar Sequências de Tarefas")
        
        if not tarefas_recorrentes:
            st.info("Não há tarefas recorrentes cadastradas.")
        else:
            st.write("Aqui você pode editar manualmente a sequência de dias consecutivos para tarefas que já vêm sendo realizadas há algum tempo.")
            st.write("Use esta funcionalidade para registrar históricos anteriores ao uso do sistema.")
            
            for i, tarefa in enumerate(tarefas_recorrentes):
                st.subheader(f"{i+1}. {tarefa['descricao']}")
                
                # Inicializar no histórico se não existir
                if tarefa["id"] not in historico:
                    historico[tarefa["id"]] = {
                        "datas": [],
                        "sequencia_atual": 0,
                        "sequencia_editada": False,
                        "recorde_sequencia": 0
                    }
                
                info_tarefa = historico[tarefa["id"]]
                sequencia_atual = info_tarefa.get("sequencia_atual", 0)
                sequencia_editada = info_tarefa.get("sequencia_editada", False)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    nova_sequencia = st.number_input(
                        f"Sequência atual de dias consecutivos",
                        min_value=0,
                        value=sequencia_atual,
                        step=1,
                        key=f"edit_seq_{i}"
                    )
                
                with col2:
                    novo_recorde = st.number_input(
                        f"Recorde de dias consecutivos",
                        min_value=0,
                        value=info_tarefa.get("recorde_sequencia", 0),
                        step=1,
                        key=f"edit_rec_{i}"
                    )
                
                with col3:
                    if st.button("Salvar", key=f"save_seq_{i}"):
                        historico[tarefa["id"]]["sequencia_atual"] = nova_sequencia
                        historico[tarefa["id"]]["sequencia_editada"] = True
                        historico[tarefa["id"]]["recorde_sequencia"] = novo_recorde
                        st.success(f"Dados atualizados com sucesso!")
                        salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                
                # Botão para reset (voltar ao cálculo automático)
                if sequencia_editada:
                    if st.button("Voltar ao cálculo automático", key=f"reset_seq_{i}"):
                        historico[tarefa["id"]]["sequencia_editada"] = False
                        historico[tarefa["id"]]["sequencia_atual"] = calcular_sequencia(historico, tarefa["id"])
                        st.success("Sequência voltou a ser calculada automaticamente.")
                        salvar_dados(tarefas_recorrentes, backlog, historico, tarefas_dia, projetos)
                
                st.divider()

# Executar a aplicação
if __name__ == "__main__":
    main()