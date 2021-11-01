import os

from trame import start, update_state, change
from trame.html import vuetify, vtk
from trame.layouts import SinglePage

from vtkmodules.vtkIOXML import vtkXMLImageDataReader
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkPolyDataMapper,
    vtkActor,
)

# VTK factory initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
import vtkmodules.vtkRenderingOpenGL2  # noqa

# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

data_directory = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)
head_vti = os.path.join(data_directory, "head.vti")

reader = vtkXMLImageDataReader()
reader.SetFileName(head_vti)
reader.Update()

contour = vtkContourFilter()
contour.SetInputConnection(reader.GetOutputPort())
contour.SetComputeNormals(1)
contour.SetComputeScalars(0)

# Extract data range => Update store/state
data_range = reader.GetOutput().GetPointData().GetScalars().GetRange()
contour_value = 0.5 * (data_range[0] + data_range[1])
update_state("data_range", data_range)
update_state("contour_value", contour_value)

# Configure contour with valid values
contour.SetNumberOfContours(1)
contour.SetValue(0, contour_value)

# Rendering setup
renderer = vtkRenderer()
renderWindow = vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

mapper = vtkPolyDataMapper()
actor = vtkActor()
mapper.SetInputConnection(contour.GetOutputPort())
actor.SetMapper(mapper)
renderer.AddActor(actor)
renderer.ResetCamera()
renderWindow.Render()

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@change("contour_value")
def update_contour(contour_value, **kwargs):
    contour.SetValue(0, contour_value)
    html_view.update_image()


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------
html_view = vtk.VtkRemoteLocalView(
    renderWindow,
    namespace="demo",
    # second arg is to force the view to start in "local" mode
    mode=("override === 'auto' ? demoMode : override", "local"),
)

layout = SinglePage("VTK contour - Remote/Local rendering")
layout.title.content = "Contour Application - Remote rendering"
layout.logo.click = "$refs.demo.resetCamera()"

with layout.toolbar:
    vuetify.VSpacer()
    vuetify.VBtnToggle(
        v_model=("override", "auto"),
        dense=True,
        mandatory=True,
        children=[
            vuetify.VBtn(vuetify.VIcon("mdi-autorenew"), value="auto"),
            vuetify.VBtn(vuetify.VIcon("mdi-rotate-3d"), value="local"),
            vuetify.VBtn(vuetify.VIcon("mdi-image"), value="remote"),
        ],
    )
    vuetify.VSpacer()
    vuetify.VSlider(
        v_model="contour_value",
        min=("data_range[0]",),
        max=("data_range[1]",),
        hide_details=True,
        dense=True,
        style="max-width: 300px",
        start="trigger('demoAnimateStart')",
        end="trigger('demoAnimateStop')",
    )
    vuetify.VSwitch(
        v_model="$vuetify.theme.dark",
        hide_details=True,
    )

    with vuetify.VBtn(icon=True, click="$refs.demo.resetCamera()"):
        vuetify.VIcon("mdi-crop-free")

    vuetify.VProgressLinear(
        indeterminate=True,
        absolute=True,
        bottom=True,
        active=("busy",),
    )

with layout.content:
    vuetify.VContainer(
        fluid=True,
        classes="pa-0 fill-height",
        children=[html_view],
    )

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    start(layout, on_ready=html_view.update_geometry)