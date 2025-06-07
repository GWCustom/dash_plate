import plotly.graph_objects as go

def plate_figure(
    values=None,
    colors=None,
    overlay_text=None,
    n_rows=8,
    n_columns=12,
    marker=None,
    scale=1.0,
    marker_size=None,
    showscale=False,
    text_size=None,
    text_color="black",
    **kwargs
) -> go.Figure:
    
    n_wells = n_rows * n_columns

    # Helper to pad or validate list input
    def pad_or_check(name, lst):
        if lst is None:
            return [None] * n_wells
        if len(lst) > n_wells:
            raise ValueError(f"{name} length ({len(lst)}) exceeds total wells ({n_wells}).")
        return lst + [None] * (n_wells - len(lst))

    # Prepare values
    values = pad_or_check("values", values)

    # Handle overlay_text
    overlay_text = pad_or_check("overlay_text", overlay_text)

    # Handle colors
    using_custom_colors = colors is not None
    if using_custom_colors:
        colors = pad_or_check("colors", colors)
        # If using literal color values, ensure all entries are valid CSS or rgba
        if all(isinstance(c, (str, type(None))) for c in colors):
            colors = ['rgba(0,0,0,0)' if c is None else c for c in colors]
    else:
        colors = [0 if val is None else val for val in values]

    # Well coordinates and hovertext
    row_labels = [chr(ord('A') + i) for i in range(n_rows)]
    col_labels = list(range(1, n_columns + 1))
    x_offset = 0.4
    label_pad = 0.08 * scale

    x, y, hovertext = [], [], []
    for i, row in enumerate(row_labels):
        for j, col in enumerate(col_labels):
            x.append(col + x_offset)
            y.append(n_rows - i)
            label = f"{row}{col}"
            val = values[i * n_columns + j]
            hovertext.append(f"{label}<br>{val}" if val is not None else label)

    if marker_size is None:
        marker_size = min(60, int(500 / max(n_rows, n_columns)))

    # Construct marker
    if marker is None:
        marker = dict(
            size=marker_size,
            symbol='circle',
            color=colors,
            line=dict(color='black', width=1),
        )
        if using_custom_colors:
            marker['showscale'] = False
        else:
            marker['colorscale'] = 'Blues'
            marker['showscale'] = showscale
            if showscale:
                marker['colorbar'] = dict(title="Value")
    else:
        marker = marker.copy()
        marker.setdefault("size", marker_size)
        marker.setdefault("line", {}).setdefault("width", 1)
        marker.setdefault("color", colors)

    scatter = go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=marker,
        hovertext=hovertext,
        hoverinfo='text',
        **kwargs
    )

    font_size = min(14, int(160 / max(n_rows, n_columns)))
    annotations = []
    for col in col_labels:
        annotations.append(dict(
            x=col + x_offset,
            y=n_rows + 0.4,
            text=str(col),
            showarrow=False,
            font=dict(size=font_size),
            yanchor='bottom'
        ))
    for i, row in enumerate(row_labels):
        annotations.append(dict(
            x=0.5 + label_pad,
            y=n_rows - i,
            text=row,
            showarrow=False,
            font=dict(size=font_size),
            xanchor='left'
        ))

    left_x = 0.5
    right_x = n_columns + x_offset + 0.5
    border_width = 4
    gray_frame_width = 2

    shapes = [
        dict(type='rect', x0=0.62 + x_offset, x1=n_columns + x_offset + 0.38,
             y0=0.72, y1=n_rows + 0.38, line=dict(color='darkgray', width=gray_frame_width), layer='below'),
        dict(type='line', x0=left_x, y0=0.5, x1=right_x, y1=0.5, line=dict(color='black', width=border_width), layer='below'),
        dict(type='line', x0=left_x, y0=0.5, x1=left_x, y1=n_rows + 0.5, line=dict(color='black', width=border_width), layer='below'),
        dict(type='line', x0=left_x, y0=n_rows + 0.5, x1=left_x + 0.5, y1=n_rows + 1.0, line=dict(color='black', width=border_width), layer='below'),
        dict(type='line', x0=left_x + 0.5, y0=n_rows + 1.0, x1=right_x, y1=n_rows + 1.0, line=dict(color='black', width=border_width), layer='below'),
        dict(type='line', x0=right_x, y0=0.5, x1=right_x, y1=n_rows + 1.0, line=dict(color='black', width=border_width), layer='below'),
    ]

    x_pad, y_pad = 1.0, 1.0
    margin = dict(
        l=scale * (20 + 5 * n_rows),
        r=scale * 20,
        t=scale * 20,
        b=scale * 20
    )
    cell_px = 60 * scale
    width = int(cell_px * n_columns + margin["l"] + margin["r"])
    height = int(cell_px * n_rows + margin["t"] + margin["b"])

    layout = dict(
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[left_x - x_pad, right_x + x_pad]),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0.5 - y_pad, n_rows + 1.0 + y_pad]),
        annotations=annotations,
        shapes=shapes,
        plot_bgcolor='white',
        margin=margin,
        width=width,
        height=height,
    )

    fig = go.Figure(data=[scatter], layout=layout)

    # Optional overlay text
    if overlay_text is not None:
        if isinstance(overlay_text, str) and overlay_text == "values":
            overlay_text = [str(v) if v is not None else "" for v in values]
        if text_size is None:
            text_size = font_size - 2
        text_trace = go.Scatter(
            x=x,
            y=y,
            mode="text",
            text=overlay_text,
            textposition="middle center",
            textfont=dict(size=text_size, color=text_color),
            hoverinfo='skip',
            showlegend=False
        )
        fig.add_trace(text_trace)

    return fig
