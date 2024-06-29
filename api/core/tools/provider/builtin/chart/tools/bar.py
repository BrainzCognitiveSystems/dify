import io
from typing import Any, Union

import matplotlib.pyplot as plt

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class BarChartTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) \
          -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        data = tool_parameters.get('data', '')
        if not data:
            return self.create_text_message('Please input data')

        title = tool_parameters.get('title', "...Here is the Title...")
        legend_loc = tool_parameters.get('legend_loc', "upper right")
        stack_values = tool_parameters.get('stack_values', None)
        graph_style = tool_parameters.get('graph_style', 'line')

        data = data.replace('\r\n', '::')
        data = data.replace('\n', '::')
        rows = data.split('::')
        data = [row.split(';') for row in rows]

        # data = [ [ 10,15,8],[3,5,7],[18,13,4] ]
        
        # # if all data is int, convert to int, otherwise float
        if all( all(i.isdigit() for i in row) for row in data):
            print("converting to 'int'")
            data = [ [int(i) for i in row] for row in data]
        else:
            print("converting to 'float'")
            data = [ [float(i) for i in row] for row in data]

        axis = tool_parameters.get('x_axis') or None
        if axis:
            axis = axis.split(';')
            if len(axis) != len(data):
                axis = None

        ## Using Matplotlib to create a bar chart
        ## ======================================
        fig, ax = plt.subplots(figsize=(12, 10))
# example
# ax.bar(x-0.2, y, width=0.2, color='b', align='center')
# ax.bar(x, z, width=0.2, color='g', align='center')
# ax.bar(x+0.2, k, width=0.2, color='r', align='center')
        width = 0.8/len(data)

        if axis:
            axis = [label[:10] + '...' if len(label) > 10 else label for label in axis]
            ax.set_xticklabels(axis, rotation=45, ha='right')
        else:
            axis = range(len(data[0]))

        if graph_style == 'bar':
            of7 = - (len(data)-1)*width/2
        else: of7 = 0
        axis = [ 1+x+of7 for x in axis]
        for row in data:
            if stack_values:
                ax.bar(axis, row, width=width, bottom=stack_values)
                stack_values = [a+b for a,b in zip(stack_values, row)]
            else:
                if graph_style == 'bar':
                    ax.bar(axis, row, width=width)
                    axis = [ x+width for x in axis]
                else: # 'line'
                    ax.plot(axis, row)
            
        if title:
            ax.set_title(title)
        if legend_loc:
            ax.legend(loc=legend_loc)

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        return [
            self.create_text_message('the bar chart is saved as an image.'),
            self.create_blob_message(blob=buf.read(),
                                    meta={'mime_type': 'image/png'})
        ]
    