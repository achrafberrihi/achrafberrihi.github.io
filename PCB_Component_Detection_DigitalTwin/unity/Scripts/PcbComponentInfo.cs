// Click a component in Play mode to see its designator, type, confidence, status and notes.
using UnityEngine;

public class PcbComponentInfo : MonoBehaviour
{
    public TwinComponent data;
    static PcbComponentInfo selected;

    void OnMouseDown() => selected = this;

    void OnGUI()
    {
        if (selected != this || data == null) return;
        string notes = data.notes != null && data.notes.Count > 0 ? string.Join("\n• ", data.notes) : "none";
        string text = $"<b>{data.@ref}</b>  ({data.type})\n" +
                      $"Confidence: {data.confidence:P0}\n" +
                      $"Status: {data.status.ToUpper()}\n" +
                      $"Position: {data.x_mm:F1} mm, {data.y_mm:F1} mm\n" +
                      $"Notes:\n• {notes}";
        var style = new GUIStyle(GUI.skin.box) { richText = true, alignment = TextAnchor.UpperLeft, fontSize = 14,
                                                  padding = new RectOffset(10, 10, 8, 8), wordWrap = true };
        GUI.Box(new Rect(16, 16, 340, 160), text, style);
    }
}
