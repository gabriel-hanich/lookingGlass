from importlib.metadata import version
import sys
import click
import glass.util as util

@click.command("diagram")
@click.option("includeProjects", "--projects", is_flag=True, default=False)
@click.pass_context
def generateMermaidDiagram(ctx, includeProjects):
    "Generates a diagram in the syntax of Mermaid.JS of your file tree"
    mermaidStr = "graph TD;\n"
    levels = ["area","category", "subfolder"]
    if includeProjects:
        levels.append("project")
    mermaidIds = {}
    a = 0
    for level in levels:
        for pathID in ctx.obj['ids']:
            if ctx.obj['ids'][pathID].idType == level:
                mermaidIds[pathID] = f"id{a}" 
                mermaidStr += f"id{a}({ctx.obj['ids'][pathID].descriptor})\n" 
                a += 1

    for pathID in ctx.obj['ids']:
        thisID = ctx.obj['ids'][pathID]
        if thisID.idType not in ["area", "child-project"]:
            if (thisID.idType == "project") and includeProjects:
                parentID = thisID.getHigherLevel(levels[levels.index(thisID.idType)-1])
                mermaidStr += f"{mermaidIds[parentID]}-->{mermaidIds[thisID.idText]}\n"
            elif thisID.idType != "project":
                parentID = thisID.getHigherLevel(levels[levels.index(thisID.idType)-1])
                mermaidStr += f"{mermaidIds[parentID]}-->{mermaidIds[thisID.idText]}\n"

    click.echo(mermaidStr)

@click.command("bg")
@click.pass_context
def manuallyDoBackgroundTasks(ctx):
    "Manually perform the background tasks"
    util.doBackgroundTasks(
            ctx.obj['root'],
            ctx.obj['metafiles'],
            ctx.obj['excludeDirs'],
            " ".join(sys.argv), 
            version('glass'),
        )