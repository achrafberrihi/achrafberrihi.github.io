// PCB digital twin for Unity.
// Builds a 3D board from the "pcb-digital-twin/1" JSON produced by inspect_board.py or the n8n workflow.
// 1 Unity unit = 1 cm. Board lies on the X/Z plane, components sit on top (Y up).
//
// Setup: attach to an empty GameObject, assign prefabs (optional, cubes are used otherwise),
// and either keep the sample file in StreamingAssets or set n8nWebhookUrl + imageUrl for live inspection.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

[Serializable] public class TwinBoard { public string name; public float width_mm; public float height_mm; }

[Serializable] public class TwinComponent
{
    public string @ref; public string type; public string prefab;
    public float x_mm; public float y_mm; public float width_mm; public float length_mm; public float rotation_deg;
    public string status; public string color; public float confidence; public List<string> notes;
}

[Serializable] public class TwinFinding { public string severity; public string @ref; public string message; }

[Serializable] public class DigitalTwin
{
    public string schema; public TwinBoard board; public int quality_score;
    public List<TwinComponent> components; public List<TwinFinding> findings;
}

[Serializable] class InspectionResponse { public DigitalTwin digital_twin; public string explanation; }

[Serializable] public class PrefabEntry { public string name; public GameObject prefab; }

public class PcbDigitalTwin : MonoBehaviour
{
    [Header("Source")]
    [Tooltip("File in Assets/StreamingAssets used when no webhook is configured.")]
    public string sampleFile = "digital_twin_sample.json";
    [Tooltip("n8n 'pcb-inspect' webhook URL, e.g. https://your-n8n/webhook/pcb-inspect")]
    public string n8nWebhookUrl = "";
    public string imageUrl = "";
    public float boardWidthMm = 100f;

    [Header("Look")]
    public List<PrefabEntry> prefabs = new List<PrefabEntry>();
    public Material boardMaterial;
    public float boardThicknessMm = 1.6f;
    public float componentHeightMm = 1.5f;

    public DigitalTwin Twin { get; private set; }
    public string Explanation { get; private set; } = "";

    const float MmToUnits = 0.1f;   // 1 unit = 1 cm
    Transform root;

    IEnumerator Start()
    {
        if (!string.IsNullOrEmpty(n8nWebhookUrl) && !string.IsNullOrEmpty(imageUrl))
            yield return StartCoroutine(InspectLive());
        else
            LoadFromStreamingAssets();
        if (Twin != null) Build();
    }

    void LoadFromStreamingAssets()
    {
        string path = Path.Combine(Application.streamingAssetsPath, sampleFile);
        if (!File.Exists(path)) { Debug.LogError($"Digital twin file not found: {path}"); return; }
        Twin = Parse(File.ReadAllText(path));
    }

    IEnumerator InspectLive()
    {
        string body = JsonUtility.ToJson(new LiveRequest { image_url = imageUrl, board_width_mm = boardWidthMm });
        using (var req = new UnityWebRequest(n8nWebhookUrl, "POST"))
        {
            req.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(body));
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Inspection failed: {req.error}. Falling back to the sample file.");
                LoadFromStreamingAssets();
                yield break;
            }
            var resp = JsonUtility.FromJson<InspectionResponse>(req.downloadHandler.text);
            Twin = resp.digital_twin;
            Explanation = resp.explanation ?? "";
        }
    }

    [Serializable] class LiveRequest { public string image_url; public float board_width_mm; }

    public static DigitalTwin Parse(string json)
    {
        var twin = JsonUtility.FromJson<DigitalTwin>(json);
        if (twin == null || twin.board == null) throw new ArgumentException("Not a pcb-digital-twin JSON");
        return twin;
    }

    public void Build()
    {
        if (root != null) Destroy(root.gameObject);
        root = new GameObject($"PCB_{Twin.board.name}").transform;
        root.SetParent(transform, false);

        float w = Twin.board.width_mm * MmToUnits, d = Twin.board.height_mm * MmToUnits;
        float t = boardThicknessMm * MmToUnits;

        var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
        board.name = "Board";
        board.transform.SetParent(root, false);
        board.transform.localScale = new Vector3(w, t, d);
        var boardRenderer = board.GetComponent<Renderer>();
        if (boardMaterial != null) boardRenderer.sharedMaterial = boardMaterial;
        else boardRenderer.material.color = new Color(0.12f, 0.32f, 0.19f);   // solder-mask green

        foreach (var c in Twin.components) SpawnComponent(c, w, d, t);
        Debug.Log($"PCB twin built: {Twin.components.Count} components, quality {Twin.quality_score}/100, " +
                  $"{Twin.findings.Count} findings");
    }

    void SpawnComponent(TwinComponent c, float boardW, float boardD, float boardT)
    {
        GameObject prefab = prefabs.Find(p => p.name == c.prefab)?.prefab;
        GameObject go = prefab != null ? Instantiate(prefab) : GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = $"{c.@ref}_{c.type}";
        go.transform.SetParent(root, false);

        float h = componentHeightMm * MmToUnits;
        // Twin origin is the bottom-left corner of the board, Unity board is centred on the root.
        go.transform.localPosition = new Vector3(c.x_mm * MmToUnits - boardW / 2, boardT / 2 + h / 2,
                                                 c.y_mm * MmToUnits - boardD / 2);
        if (prefab != null)
        {
            // Prefabs are modelled along X, so tall footprints are turned 90°.
            go.transform.localRotation = Quaternion.Euler(0, c.rotation_deg, 0);
        }
        else
        {
            // Placeholder cube: the detected footprint is already axis-aligned, so scale it directly.
            go.transform.localScale = new Vector3(c.width_mm * MmToUnits, h, c.length_mm * MmToUnits);
        }

        if (ColorUtility.TryParseHtmlString(c.color, out var color))
            foreach (var r in go.GetComponentsInChildren<Renderer>()) r.material.color = color;

        if (go.GetComponent<Collider>() == null) go.AddComponent<BoxCollider>();
        go.AddComponent<PcbComponentInfo>().data = c;
    }
}
