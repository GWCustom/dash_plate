import plotly.graph_objects as go
import re
import pandas as pd
from typing import Optional, Dict, List, Union


class Plate:

    def __init__(
        self,
        values=None,
        colors=None,
        overlay_text=None,
        n_rows=8,
        n_columns=12,
        fill_direction="horizontal"
    ):
        self.values = values
        self.colors = colors
        self.overlay_text = overlay_text
        self.n_rows = n_rows
        self.n_columns = n_columns
        self.fill_direction = fill_direction

    def plot(self, **kwargs) -> go.Figure:
        return self._plate_figure(
            values=self.values,
            colors=self.colors,
            overlay_text=self.overlay_text,
            n_rows=self.n_rows,
            n_columns=self.n_columns,
            fill_direction=self.fill_direction,
            **kwargs
        )

    @classmethod
    def from_dict(
        cls,
        well_dict: Dict[str, Dict[str, Union[float, str]]],
        n_rows: int = 8,
        n_columns: int = 12
    ) -> "Plate":
        def normalize_well(w):
            match = re.match(r"([A-Ha-h])0*(\d+)", w)
            if not match:
                raise ValueError(f"Invalid well name: {w}")
            row, col = match.groups()
            return row.upper(), int(col)

        values = [None] * (n_rows * n_columns)
        colors = [None] * (n_rows * n_columns)
        text = [None] * (n_rows * n_columns)

        for well, content in well_dict.items():
            row_char, col_num = normalize_well(well)
            row_idx = ord(row_char) - ord('A')
            col_idx = col_num - 1
            if row_idx >= n_rows or col_idx >= n_columns:
                continue

            idx = row_idx * n_columns + col_idx

            values[idx] = content.get("value")
            colors[idx] = content.get("color")
            text[idx] = content.get("text")

        return cls(values, colors, text, n_rows=n_rows, n_columns=n_columns, fill_direction="horizontal")

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        well_col="well",
        value_col="value",
        color_col="color",
        text_col="text",
        n_rows: int = 8,
        n_columns: int = 12
    ) -> "Plate":
        record_dict = {
            row[well_col]: {
                "value": row.get(value_col),
                "color": row.get(color_col),
                "text": row.get(text_col),
            }
            for _, row in df.iterrows()
        }
        return cls.from_dict(record_dict, n_rows=n_rows, n_columns=n_columns, fill_direction="horizontal")

    @staticmethod
    def _plate_figure(
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
        fill_direction="horizontal",
        **kwargs
    ) -> go.Figure:

        n_wells = n_rows * n_columns

        def pad_or_check(name, lst):
            if lst is None:
                return [None] * n_wells
            if len(lst) > n_wells:
                raise ValueError(f"{name} length ({len(lst)}) exceeds total wells ({n_wells}).")
            return lst + [None] * (n_wells - len(lst))

        values = pad_or_check("values", values)
        overlay_text = pad_or_check("overlay_text", overlay_text)

        using_custom_colors = colors is not None
        if using_custom_colors:
            colors = pad_or_check("colors", colors)
            if all(isinstance(c, (str, type(None))) for c in colors):
                colors = ['rgba(0,0,0,0)' if c is None else c for c in colors]
        else:
            colors = [0 if v is None else v for v in values]

        row_labels = [chr(ord('A') + i) for i in range(n_rows)]
        col_labels = list(range(1, n_columns + 1))
        x_offset = 0.4
        label_pad = 0.08 * scale

        x, y, hovertext = [], [], []
        for i, row in enumerate(row_labels):
            for j, col in enumerate(col_labels):
                idx = i * n_columns + j
                x.append(col + x_offset)
                y.append(n_rows - i)
                label = f"{row}{col}"
                val = values[idx]
                hovertext.append(f"{label}<br>{val}" if val is not None else label)

        if marker_size is None:
            marker_size = min(60, int(500 / max(n_rows, n_columns)))

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
            showlegend=False,
        )

        fig = go.Figure(data=[scatter], layout=layout)

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
