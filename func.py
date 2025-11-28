import io
import json
import oci
import time
import smtplib
import email.utils
import subprocess
import datetime
import pytz
import re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText




#
# ===============================================================
#  AUTENTICAÇÃO VIA RESOURCE PRINCIPAL (OBRIGATÓRIO NO OCI FUNCTION)
# ===============================================================
#
def get_resource_principal_signer():
    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        config = {"region": signer.region}
        return config, signer
    except Exception as ex:
        raise Exception("Erro ao obter Resource Principal: " + str(ex))

# ========================================================================
# GERAR ATA DE REUNIÃO USANDO OCI GENERATIVE AI (COM RETRY SEGURO)
# ========================================================================
def gerar_ata_reuniao(input_text: str):


    # 🔹 Auth via Resource Principal
    config, signer = get_resource_principal_signer()

    # 🔹 Compartment
    compartment_id = "ocid1.compartment.oc1..aaaaaaaa3c2l7izkhnx35oflzpt62nfs4wb6e43ieivized3xldvfyfefz6a"

    # 🔹 Endpoint GenAI
    endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

    # 🔹 Cliente Generative AI
    client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,
        signer=signer,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(15, 300)
    )

    # ==================================================
    # TEMPLATE HTML
    # ==================================================

    
    template_html = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Ata de Reunião - [Titulo da ATA de Reunião]</title><style type="text/css">body{font-family:Arial,sans-serif;background-color:#f5f5f5;color:#333;margin:0;padding:20px}.email-container{max-width:600px;margin:0 auto;background-color:#ffffff;border:1px solid #ccc;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.1)}.header{background-color:#8B0000;color:#ffffff;padding:20px;text-align:center}.header h1{margin:0;font-size:24px}.content{padding:20px;background-color:#f9f9f9;color:#555}.original-text{background-color:#e0e0e0;padding:15px;border-left:4px solid #8B0000;margin-bottom:20px;font-style:italic}.ata-section{background-color:#ffffff;padding:15px;border:1px solid #ddd;border-radius:5px;margin-bottom:15px}.ata-section h2{color:#8B0000;border-bottom:2px solid #8B0000;padding-bottom:5px}.footer{background-color:#8B0000;color:#ffffff;text-align:center;padding:10px;font-size:12px}table{width:100%;border-collapse:collapse;margin:10px 0}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background-color:#f2f2f2;color:#333}</style></head><body><div class="email-container"><div class="header"><h1>Ata de Reunião - [Titulo da ATA de Reunião]</h1><p>Data: [Insira a data da reunião, ex: 15/10/2023] | Local: Reunião Virtual/Presencial</p></div><div class="content"><p>Prezado(a) Equipe,</p><p>[Introducao exemplo: Segue em anexo a ata da reunião realizada hoje, baseada nas discussões sobre o levantamento de requisitos. Para transparência, o texto original das anotações da reunião está preservado abaixo, seguido da versão formalizada da ata.]</p><div class="original-text"><strong>Texto Original das Anotações:</strong><br>""" + input_text + """</div><div class="ata-section"><h2>1. Participantes</h2><p>[Insira os nomes dos participantes, ex: Equipe de Desenvolvimento, Representante do Cliente].</p></div><div class="ata-section"><h2>2. Objetivo da Reunião</h2><p>[Objetivo exemplo: Discutir o levantamento de requisitos do projeto, identificar problemas no serviço atual e propor soluções para maior resiliência.]</p></div><div class="ata-section"><h2>3. Principais Pontos Discutidos</h2><ul><li>[Principais Pontos Discutidos exemplos: Realização do levantamento de requisitos, que revelou grandes problemas no serviço atual.]</li></ul></div><div class="ata-section"><h2>4. Decisões Tomadas</h2><table><tr><th>Ação</th><th>Responsável</th><th>Prazo</th></tr><tr><td>[Elaborar orçamento detalhado para os 11 DR, priorizando opções de baixo custo.]</td><td>[Nome do Responsável, ex: Gerente de Projetos]</td><td>[Prazo, ex: 10/11/2023]</td></tr><tr><td>[Agendar próxima reunião com o cliente para apresentar alternativas econômicas.]</td><td>[Nome do Responsável, ex: Equipe Comercial]</td><td>[Prazo, ex: 20/10/2023]</td></tr></table></div><div class="ata-section"><h2>5. Próximos Passos</h2><p>[Próximos Passos exemplo:Refinar as propostas de DR com foco em custo-benefício e preparar apresentação para o cliente. Manter comunicação aberta para ajustes necessários.]</p></div><p>[Esta ata foi elaborada com base nas discussões realizadas. Caso haja alguma observação ou correção, favor informar em até 48 horas.]</p><p>Atenciosamente,<br>[Seu Nome]<br>[Sua Posição]<br>[Contato: Email e Telefone]</p></div><div class="footer"><p>Este email foi enviado automaticamente. Por favor, não responda diretamente a esta mensagem.</p></div></div></body></html>"""

    # ==================================================
    # PROMPT
    # ==================================================
    content = oci.generative_ai_inference.models.TextContent()
    content.text = (
        "Faça uma ATA de reunião com esse texto preenchendo os tópicos do HTML como "
        "Data, Participantes, Objetivo da Reunião, Principais Pontos Discutidos, "
        "Decisões Tomadas e Próximos Passos. "
        "USE o template abaixo exatamente como está, sem modificar estrutura. "
        "\n\nTEMPLATE HTML:\n"
        + template_html +
        "\n\nUTILIZE ESSE TEMPLETE HTML SEM (```html):\n" + input_text
    )

    message = oci.generative_ai_inference.models.Message(
        role="USER",
        content=[content]
    )

    chat_request = oci.generative_ai_inference.models.GenericChatRequest(
        api_format=oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
        messages=[message],
        max_tokens=20000,
        temperature=1,   
        frequency_penalty = 0,
        presence_penalty = 0,
        top_p = 1,
        top_k = 0
    )

    chat_detail = oci.generative_ai_inference.models.ChatDetails(
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            model_id="ocid1.generativeaimodel.oc1.us-chicago-1."
        ),
        chat_request=chat_request,
        compartment_id=compartment_id
    )

    # ==================================================
    # CHAMADA COM RETRY (while seguro)
    # ==================================================
    max_tentativas = 5
    tentativa = 1

    while tentativa <= max_tentativas:
        try:
            response = client.chat(chat_detail)
            break  # sucesso → sai do loop

        except Exception as e:
            print(f"Tentativa {tentativa} falhou: {e}")

            # ⛔ Se for erro não recuperável → parar
            if "invalid" in str(e).lower():
                raise e

            # ⏳ Aguardar antes de tentar novamente
            time.sleep(2 * tentativa)

            tentativa += 1

    if tentativa > max_tentativas:
        raise Exception("Falha ao chamar o GenAI após várias tentativas.")

    # ==================================================
    # EXTRAIR TEXTO DO MODELO
    # ==================================================
    try:
        texto = response.data.chat_response.choices[0].message.content[0].text
        return texto

    except Exception as e:
        return f"Erro ao extrair texto: {e}\nRetorno bruto: {response.data}"

#
# ===============================================================
#  ENVIAR EMAIL (OCI Email Delivery)
# ===============================================================
#
SMTP_USERNAME = "ocid1.user.oc1..@ocid1.tenancy.oc1...33.com"
SMTP_PASSWORD = "AAAAAAAAA"
SMTP_HOST = "smtp.email.<REGION>.oci.oraclecloud.com"
SMTP_PORT = 587

SENDER_EMAIL = "noreply@cloud.com.br"
SENDER_NAME = "AI Audio Request"


def send_oci_email(recipient: str, subject: str, body: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email.utils.formataddr((SENDER_NAME, SENDER_EMAIL))
    msg['To'] = recipient
    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
    server.close()


#
# ===============================================================
#  OBTER ÚLTIMO ARQUIVO DO BUCKET
# ===============================================================
#
def buscar_ultimo_arquivo(namespace, bucket, client):
    lista = client.list_objects(
        namespace,
        bucket,
        fields="timeCreated"
    )

    if not lista.data.objects:
        return None

    ultimo = sorted(
        lista.data.objects,
        key=lambda x: x.time_created,
        reverse=True
    )[0]

    return ultimo.name


#
# ===============================================================
#  REMOVER ARQUIVO PELO NOME
# ===============================================================
#
def delete_object_by_name(namespace, bucket_name, object_name, client):
    try:
        client.delete_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name
        )
        print(f"Arquivo removido: {object_name}")

    except oci.exceptions.ServiceError as e:
        print(f"Erro ao remover: {e}")


#
# ===============================================================
#  DELETAR JOB (AGORA COM SDK, NÃO MAIS CLI)
# ===============================================================
#
def delete_transcription_job(job_id, ai_client):
    try:
        ai_client.delete_transcription_job(
            transcription_job_id=job_id
        )
        print(f"Job deletado: {job_id}")
    except Exception as ex:
        print(f"Erro ao deletar job: {str(ex)}")


#
# ===============================================================
#  PROCESSAR STRING DO NOME DO ARQUIVO
# ===============================================================
#
def processar_string_email_corrigido(nome):
    partes = nome.rsplit(".", 1)
    base = partes[0]
    extensao = "." + partes[1]

    partes_email_data = base.rsplit("-", 1)
    email_parte = partes_email_data[0]
    data = partes_email_data[1]

    email = email_parte.replace("-oracle.com", "@oracle.com")

    timestamp_s = int(data) / 1000
    data_utc = datetime.datetime.fromtimestamp(timestamp_s, tz=datetime.timezone.utc)

    return {
        "Email": email,
        "User": email.split("@")[0],
        "Data": data_utc.strftime('%Y-%m-%d %H:%M:%S'),
        "Extensao": extensao
    }


#
# ===============================================================
#  FUNÇÃO PRINCIPAL
# ===============================================================
#
def handler(ctx, data: io.BytesIO = None):

    print("### OCI FUNCTION STARTED ###")

    # Auth
    config, signer = get_resource_principal_signer()

    object_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
    ai_speech = oci.ai_speech.AIServiceSpeechClient(config, signer=signer)

    namespace = "objectstorage-namespace"
    bucket_name = "speech-in"
    bucket_output = "speech-out"
    compartment_id = "ocid1.compartment.oc1.."

    # 1) Buscar último arquivo
    ultimo = buscar_ultimo_arquivo(namespace, bucket_name, object_client)
    print("Último arquivo encontrado:", ultimo)

    info = processar_string_email_corrigido(ultimo)

    # 2) Criar job
    job_details = oci.ai_speech.models.CreateTranscriptionJobDetails(
        display_name="function_auto_transcribe",
        compartment_id=compartment_id,
        model_details=oci.ai_speech.models.TranscriptionModelDetails(
            domain="GENERIC",
            language_code="pt",
            model_type="WHISPER_MEDIUM"
        ),
        input_location=oci.ai_speech.models.ObjectListInlineInputLocation(
            location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
            object_locations=[
                oci.ai_speech.models.ObjectLocation(
                    namespace_name=namespace,
                    bucket_name=bucket_name,
                    object_names=[ultimo]
                )
            ]
        ),
        output_location=oci.ai_speech.models.OutputLocation(
            namespace_name=namespace,
            bucket_name=bucket_output,
            prefix=info["Email"]
        )
    )

    job = ai_speech.create_transcription_job(job_details).data
    job_id = job.id
    print("Job criado:", job_id)

    # 3) Aguardar terminar
    print("\n⏳ Aguardando processamento...")
    while True:
        estado = ai_speech.get_transcription_job(job_id).data.lifecycle_state
        print("Estado:", estado)
        if estado in ["SUCCEEDED", "FAILED", "CANCELED"]:
            break
        time.sleep(2)
    if estado != "SUCCEEDED":
        raise Exception("❌ Job não completou: " + estado)

    print("\n✔ Job finalizado com sucesso!")
    # 4) Ler JSON de saída
    short_id = job_id.split(".")[-1]
    prefix = f"{info['Email']}/job-{short_id}"
    

    lista = object_client.list_objects(
        namespace,
        bucket_output,
        prefix=prefix
    ).data.objects

    json_files = [o.name for o in lista if o.name.endswith(".json")]

    if not json_files:
        raise Exception("Nenhum JSON encontrado na saída")

    # 5) Baixar JSON final
    response = object_client.get_object(namespace, bucket_output, json_files[0])
    conteudo = json.loads(response.data.content)

    print("\n===================== TRANSCRIÇÃO =====================")
    transcript = conteudo["transcriptions"][0]["transcription"]
    print("=======================================================")

    print("\n===================== GENAI =====================")
    transcript_final=gerar_ata_reuniao(transcript)
    print("=======================================================")
    

    # 6) Enviar e-mail
    send_oci_email(info["Email"], "Transcrição Concluída", transcript_final)

    # 7) Remover arquivo original
    delete_object_by_name(namespace, bucket_name, ultimo, object_client)

    # 8) Deletar job
    delete_transcription_job(job_id, ai_speech)

    return json.dumps({
        "status": "OK",
        "file": ultimo,
        "email": info["Email"],
        "transcription_length": len(transcript)
    })
