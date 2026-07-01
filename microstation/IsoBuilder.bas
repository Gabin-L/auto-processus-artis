Attribute VB_Name = "IsoBuilder"
' =============================================================================
' IsoBuilder - generation automatique d'une mise en plan isometrique MicroStation
' =============================================================================
' Consomme le JSON produit par iso_engine (voir /iso_engine/export.py). Ce
' script ne calcule AUCUNE geometrie : tout (coordonnees 2D, longueurs
' reelles a coter, numeros de soudure, nomenclature) est deja calcule cote
' Python. Le role de la macro se limite a placer des elements MicroStation.
'
' PREREQUIS avant de lancer BuildIsoFromJson (a faire une seule fois) :
'   1. Un fichier germe (seed file) "seed_iso.dgn" avec les niveaux,
'      cotations, styles de texte et cartouche deja en place.
'   2. Une bibliotheque de cellules attachee contenant au minimum les
'      cellules dont le nom correspond aux valeurs de "fitting_type" du
'      JSON (ex: ELBOW90, TEE, VALVE_GATE, REDUCER_CONCENTRIC...). Adapter
'      la fonction CellNameFor ci-dessous au nommage reel de votre
'      bibliotheque.
'   3. Un niveau ("Level") par type d'element (tuyauterie, cotation,
'      soudures, nomenclature, cartouche) - noms configurables ci-dessous.
'
' LIMITES CONNUES (voir docs/workflow.md) :
'   - Le placement de la nomenclature utilise une table de texte simple, pas
'     le generateur de table natif de MicroStation (a ameliorer si besoin).
'   - L'orientation des cellules de raccord est posee a 0 degre : pour un
'     rendu isometrique correct, il faut en general orienter chaque cellule
'     selon le troncon entrant/sortant. A affiner avec une vraie bibliotheque
'     de cellules isometriques (cellules deja dessinees dans le plan iso).
' =============================================================================

Option Explicit

Private Const LEVEL_PIPE As String = "TUYAUTERIE"
Private Const LEVEL_FITTINGS As String = "RACCORDS"
Private Const LEVEL_DIMENSIONS As String = "COTATION"
Private Const LEVEL_WELDS As String = "SOUDURES"
Private Const LEVEL_BOM As String = "NOMENCLATURE"
Private Const LEVEL_TITLEBLOCK As String = "CARTOUCHE"

Private Const TEXT_HEIGHT_MM As Double = 2.5
Private Const WELD_MARK_RADIUS_MM As Double = 1.5


' Point d'entree principal.
'   jsonPath : chemin vers le fichier JSON produit par iso_engine.export
'   seedPath : chemin vers le fichier germe (.dgn) contenant gabarit + cellules
'   outPath  : chemin du .dgn a produire
Public Sub BuildIsoFromJson(ByVal jsonPath As String, ByVal seedPath As String, ByVal outPath As String)
    Dim drawing As Object
    Set drawing = LoadDrawingJson(jsonPath)

    Dim model As DesignFile
    Set model = OpenDesignFileFromSeed(seedPath, outPath)

    DrawPipeRoute drawing, model
    PlaceFittingCells drawing, model
    PlaceWeldMarks drawing, model
    PlaceDimensions drawing, model
    PlaceBomTable drawing, model
    FillTitleBlock drawing, model

    model.Save
    MsgBox "Isometrique genere : " & outPath, vbInformation
End Sub


Private Function OpenDesignFileFromSeed(ByVal seedPath As String, ByVal outPath As String) As DesignFile
    FileCopy seedPath, outPath
    Set OpenDesignFileFromSeed = Application.OpenDesignFile(outPath)
End Function


' ---------------------------------------------------------------------------
' Trace du tuyau : une ligne (ou chaine de lignes) par troncon du JSON,
' sur le niveau tuyauterie, aux coordonnees 2D deja projetees cote Python.
' ---------------------------------------------------------------------------
Private Sub DrawPipeRoute(ByVal drawing As Object, ByVal model As DesignFile)
    Dim vertices As Object
    Set vertices = drawing("vertices")

    Dim seg As Variant
    For Each seg In drawing("segments")
        Dim startPt As Point3d, endPt As Point3d
        startPt = PointFromSeq(vertices, seg("start_seq"))
        endPt = PointFromSeq(vertices, seg("end_seq"))

        Dim line As LineElement
        Set line = CreateLineElement2(Nothing, startPt, endPt)
        line.Level = ActiveModelReference.GetLevelByName(LEVEL_PIPE)
        model.ActiveModelReference.AddElement line
    Next seg
End Sub


' ---------------------------------------------------------------------------
' Placement des cellules de raccord (coudes, tes, reductions, vannes...) aux
' points marques d'un fitting_type dans le JSON.
' ---------------------------------------------------------------------------
Private Sub PlaceFittingCells(ByVal drawing As Object, ByVal model As DesignFile)
    Dim v As Variant
    For Each v In drawing("vertices")
        If Not IsNullOrEmpty(v("fitting_type")) Then
            Dim cellName As String
            cellName = CellNameFor(CStr(v("fitting_type")))

            Dim origin As Point3d
            origin.x = MmToUor(v("x2d"))
            origin.y = MmToUor(v("y2d"))
            origin.z = 0

            Dim cell As CellElement
            Set cell = CreateCellElement2(cellName, origin, Matrix3dIdentity(), True)
            cell.Level = ActiveModelReference.GetLevelByName(LEVEL_FITTINGS)
            model.ActiveModelReference.AddElement cell

            If Not IsNullOrEmpty(v("fitting_ref")) Then
                ' Etiquette texte simple sous la cellule, memes limites que
                ' PlaceDimensions : un vrai tag attache (AttachTagSet) serait
                ' preferable mais demande un tag set deja defini dans le
                ' gabarit et n'est pas verifiable sans MicroStation reel ici.
                Dim refPt As Point3d
                refPt.x = origin.x
                refPt.y = origin.y - MmToUor(TEXT_HEIGHT_MM * 1.5)
                refPt.z = 0

                Dim refLabel As TextElement
                Set refLabel = CreateTextElement1(Nothing, CStr(v("fitting_ref")), refPt, Matrix3dIdentity())
                refLabel.Level = ActiveModelReference.GetLevelByName(LEVEL_FITTINGS)
                refLabel.TextStyle.Height = MmToUor(TEXT_HEIGHT_MM)
                refLabel.TextStyle.Width = MmToUor(TEXT_HEIGHT_MM)
                model.ActiveModelReference.AddElement refLabel
            End If
        End If
    Next v
End Sub


' Nommage des cellules : adapter a la bibliotheque reelle de l'entreprise.
' Convention par defaut : nom de cellule = fitting_type en majuscules.
Private Function CellNameFor(ByVal fittingType As String) As String
    CellNameFor = UCase(fittingType)
End Function


' ---------------------------------------------------------------------------
' Reperes de soudure : petit cercle + texte "W1", "W2"... au point concerne.
' ---------------------------------------------------------------------------
Private Sub PlaceWeldMarks(ByVal drawing As Object, ByVal model As DesignFile)
    Dim vertices As Object
    Set vertices = drawing("vertices")

    Dim w As Variant
    For Each w In drawing("welds")
        Dim pt As Point3d
        pt = PointFromSeq(vertices, w("seq"))

        Dim circle As EllipseElement
        Set circle = CreateEllipseElement2(Nothing, MmToUor(WELD_MARK_RADIUS_MM), MmToUor(WELD_MARK_RADIUS_MM), Matrix3dIdentity(), pt)
        circle.Level = ActiveModelReference.GetLevelByName(LEVEL_WELDS)
        model.ActiveModelReference.AddElement circle

        Dim lbl As TextElement
        Set lbl = CreateTextElement1(Nothing, CStr(w("weld_id")), pt, Matrix3dIdentity())
        lbl.Level = ActiveModelReference.GetLevelByName(LEVEL_WELDS)
        lbl.TextStyle.Height = MmToUor(TEXT_HEIGHT_MM)
        lbl.TextStyle.Width = MmToUor(TEXT_HEIGHT_MM)
        model.ActiveModelReference.AddElement lbl
    Next w
End Sub


' ---------------------------------------------------------------------------
' Cotation : une cote lineaire par troncon, avec la longueur REELLE mesuree
' sur le terrain (true_length_mm), pas la longueur dessinee a l'ecran.
' ---------------------------------------------------------------------------
Private Sub PlaceDimensions(ByVal drawing As Object, ByVal model As DesignFile)
    Dim vertices As Object
    Set vertices = drawing("vertices")

    Dim seg As Variant
    For Each seg In drawing("segments")
        Dim startPt As Point3d, endPt As Point3d
        startPt = PointFromSeq(vertices, seg("start_seq"))
        endPt = PointFromSeq(vertices, seg("end_seq"))

        Dim dimText As String
        dimText = Format(seg("true_length_mm"), "0") & " mm"

        Dim mid As Point3d
        mid.x = (startPt.x + endPt.x) / 2
        mid.y = (startPt.y + endPt.y) / 2
        mid.z = 0

        Dim dimLabel As TextElement
        Set dimLabel = CreateTextElement1(Nothing, dimText, mid, Matrix3dIdentity())
        dimLabel.Level = ActiveModelReference.GetLevelByName(LEVEL_DIMENSIONS)
        dimLabel.TextStyle.Height = MmToUor(TEXT_HEIGHT_MM)
        dimLabel.TextStyle.Width = MmToUor(TEXT_HEIGHT_MM)
        model.ActiveModelReference.AddElement dimLabel

        ' TODO : remplacer ce texte simple par un vrai DimensionElement
        ' MicroStation (AssociativeDimension) pour beneficier des fleches et
        ' du rattachement associatif aux points - laisse en texte brut pour
        ' que ce squelette reste lisible sans SDK de cotation complet.
    Next seg
End Sub


' ---------------------------------------------------------------------------
' Nomenclature : table texte simple placee a un point fixe de la feuille
' (coin bas droit, sous le cartouche). A remplacer par le composant table
' natif de MicroStation si le gabarit en possede un.
' ---------------------------------------------------------------------------
Private Sub PlaceBomTable(ByVal drawing As Object, ByVal model As DesignFile)
    Const BOM_ORIGIN_X_MM As Double = 250
    Const BOM_ORIGIN_Y_MM As Double = 10
    Const ROW_HEIGHT_MM As Double = 4

    Dim row As Integer
    row = 0

    Dim header As Point3d
    header.x = MmToUor(BOM_ORIGIN_X_MM)
    header.y = MmToUor(BOM_ORIGIN_Y_MM)
    header.z = 0
    PlaceBomRow "NOMENCLATURE", header, model
    row = row + 1

    Dim item As Variant
    For Each item In drawing("bom")
        Dim rowText As String
        rowText = item("description") & "  " & item("nominal_size") & "  " & _
                  item("quantity") & " " & item("unit")

        Dim pt As Point3d
        pt.x = MmToUor(BOM_ORIGIN_X_MM)
        pt.y = MmToUor(BOM_ORIGIN_Y_MM - row * ROW_HEIGHT_MM)
        pt.z = 0
        PlaceBomRow rowText, pt, model
        row = row + 1
    Next item
End Sub


Private Sub PlaceBomRow(ByVal text As String, ByVal pt As Point3d, ByVal model As DesignFile)
    Dim el As TextElement
    Set el = CreateTextElement1(Nothing, text, pt, Matrix3dIdentity())
    el.Level = ActiveModelReference.GetLevelByName(LEVEL_BOM)
    el.TextStyle.Height = MmToUor(TEXT_HEIGHT_MM)
    el.TextStyle.Width = MmToUor(TEXT_HEIGHT_MM)
    model.ActiveModelReference.AddElement el
End Sub


' ---------------------------------------------------------------------------
' Cartouche : recherche les cellules de tag existantes dans le gabarit
' (placees dans le seed file) et met a jour leurs valeurs. Suppose que le
' gabarit contient deja une cellule de cartouche avec des tags nommes
' d'apres les cles de l'en-tete (LINE_NUMBER, PROJECT_CODE, CLIENT...).
' ---------------------------------------------------------------------------
Private Sub FillTitleBlock(ByVal drawing As Object, ByVal model As DesignFile)
    Dim header As Object
    Set header = drawing("header")

    Dim key As Variant
    For Each key In header.Keys
        UpdateTagValue model, UCase(CStr(key)), CStr(header(key))
    Next key
End Sub


Private Sub UpdateTagValue(ByVal model As DesignFile, ByVal tagName As String, ByVal value As String)
    Dim el As Element
    For Each el In model.ActiveModelReference.GetLevelByName(LEVEL_TITLEBLOCK).GetElements
        If TypeOf el Is TagElement Then
            If UCase(el.AsTagElement.Name) = tagName Then
                el.AsTagElement.Value = value
                el.Rewrite
            End If
        End If
    Next el
End Sub


' =============================================================================
' Utilitaires
' =============================================================================

Private Function PointFromSeq(ByVal vertices As Object, ByVal seq As Variant) As Point3d
    Dim v As Variant
    For Each v In vertices
        If CLng(v("seq")) = CLng(seq) Then
            Dim pt As Point3d
            pt.x = MmToUor(v("x2d"))
            pt.y = MmToUor(v("y2d"))
            pt.z = 0
            PointFromSeq = pt
            Exit Function
        End If
    Next v
    Err.Raise vbObjectError + 1, "IsoBuilder", "Point seq=" & seq & " introuvable dans le JSON"
End Function


Private Function IsNullOrEmpty(ByVal v As Variant) As Boolean
    If IsNull(v) Then
        IsNullOrEmpty = True
    ElseIf IsEmpty(v) Then
        IsNullOrEmpty = True
    Else
        IsNullOrEmpty = (Len(CStr(v)) = 0)
    End If
End Function


' Convertit des millimetres en unites de resolution MicroStation (UOR) selon
' le facteur du fichier actif. Adapter si le gabarit n'utilise pas le mm
' comme unite maitre.
Private Function MmToUor(ByVal mm As Double) As Double
    MmToUor = mm * ActiveModelReference.UORsPerMasterUnit
End Function


' ---------------------------------------------------------------------------
' Chargement JSON : MicroStation VBA n'a pas de parseur JSON natif. On
' s'appuie ici sur le moteur de script Windows (ScriptControl / JScript) qui
' est disponible sur tout poste Windows avec MicroStation, sans dependance
' externe a installer.
' ---------------------------------------------------------------------------
Private Function LoadDrawingJson(ByVal jsonPath As String) As Object
    Dim raw As String
    raw = ReadTextFile(jsonPath)

    Dim sc As Object
    Set sc = CreateObject("ScriptControl")
    sc.Language = "JScript"
    sc.AddCode "function parseJson(s) { return eval('(' + s + ')'); }"

    Set LoadDrawingJson = sc.Run("parseJson", raw)
End Function


Private Function ReadTextFile(ByVal path As String) As String
    Dim fso As Object, stream As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set stream = fso.OpenTextFile(path, 1, False, -1) ' -1 = TristateTrue (Unicode)
    ReadTextFile = stream.ReadAll
    stream.Close
End Function
