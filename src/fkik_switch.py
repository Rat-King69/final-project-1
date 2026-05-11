import maya.cmds as cmds


def duplicate_chain():
    sel = cmds.ls(sl=True)

    fk_chain = cmds.duplicate(sel, renameChildren=True)
    for jnt in fk_chain:
        cmds.rename(jnt, jnt.replace('_JNT1', '_FK_JNT'))

    ik_chain = cmds.duplicate(sel, renameChildren=True)
    for jnt in ik_chain:
        cmds.rename(jnt, jnt.replace('_JNT1', '_IK_JNT'))


def create_fk_controls(sel=None):
    if sel is None:
        sel = cmds.ls(sl=True)
    
    for jnt in reversed(sel):
        short_name = jnt.split('|')[-1]
        
        if short_name.startswith('joint') and short_name[5].isdigit():
            short_name = '_'.join(short_name.split('_')[1:])

        base_name = short_name.replace('_JNT', '')

        zero = cmds.duplicate(
            jnt,
            name=base_name + '_ZERO',
            parentOnly=True
        )[0]

        jnt = cmds.rename(jnt, base_name + '_CON')

        cmds.parent(jnt, zero)

        circle = cmds.circle(normal=[1, 0, 0], ch=False)[0]
        circle_shape = cmds.listRelatives(circle, shapes=True)[0]
        cmds.parent(circle_shape, jnt, s=True, add=True)
        cmds.delete(circle)


def ik_control_setup(sel=None):
    if sel is None:
        sel = cmds.ls(sl=True, type='joint')

    ik_joints = [jnt for jnt in sel if 'IK_JNT' in jnt]
    start_jnt = ik_joints[0]
    end_jnt = ik_joints[-1]

    ik_handle, ik_effector = cmds.ikHandle(
        name='L_arm_IKH',
        startJoint=start_jnt,
        endEffector=end_jnt,
        solver='ikRPsolver'
    )

    short_name = end_jnt.split('|')[-1]
    if short_name.startswith('joint') and short_name[5].isdigit():
        short_name = '_'.join(short_name.split('_')[1:])
    base_name = short_name.replace('_IK_JNT', '')

    ik_ctrl = cmds.circle(name=base_name + '_IK_CON', normal=[1, 0, 0], radius=1, constructionHistory=False)[0]
    ik_ctrl_grp = cmds.group(ik_ctrl, name=base_name + '_GRP')
    constraint = cmds.parentConstraint(end_jnt, ik_ctrl_grp, maintainOffset=False)
    cmds.delete(constraint)
    cmds.parent(ik_handle, ik_ctrl)

    start_pos = cmds.xform(start_jnt, query=True, worldSpace=True, translation=True)
    end_pos = cmds.xform(end_jnt, query=True, worldSpace=True, translation=True)
    dist_node = cmds.distanceDimension(startPoint=start_pos, endPoint=end_pos)

    locs = cmds.ls(type='locator')
    start_loc = cmds.rename(cmds.listRelatives(locs[0], parent=True)[0], 'start_pos')
    end_loc = cmds.rename(cmds.listRelatives(locs[1], parent=True)[0], 'end_pos')

    cmds.parent(start_loc, 'L_clavicle_JNT')
    cmds.parent(end_loc, ik_ctrl)





def create_fk_ik_switch():
    sel = cmds.ls(sl=True)
    switch_ctrl = sel[0]
    bind_joints = sel[1:]

    if not cmds.attributeQuery('FK_IK', node=switch_ctrl, exists=True):
        cmds.addAttr(switch_ctrl, longName='FK_IK', attributeType='float', min=0, max=1, defaultValue=0, keyable=True)

    reverse = cmds.createNode('reverse', name='FK_IK_REV')
    cmds.connectAttr(switch_ctrl + '.FK_IK', reverse + '.inputX')

    for jnt in bind_joints:
        short = jnt.split('|')[-1]
        fk_con = short.replace('_JNT', '_FK_CON')
        ik_jnt = short.replace('_JNT', '_IK_JNT')

        blend = cmds.shadingNode('blendColors', name=short.replace('_JNT', '_BC'), asUtility=True)

        cmds.connectAttr(fk_con + '.rotate', blend + '.color1')
        cmds.connectAttr(ik_jnt + '.rotate', blend + '.color2')
        cmds.connectAttr(blend + '.output', jnt + '.rotate')
        cmds.connectAttr(reverse + '.outputX', blend + '.blender')

        scale_blend = cmds.shadingNode('blendColors', name=short.replace('_JNT', '_SCALE_BC'), asUtility=True)

        cmds.connectAttr(fk_con + '.scale', scale_blend + '.color1')
        cmds.connectAttr(ik_jnt + '.scale', scale_blend + '.color2')
        cmds.connectAttr(scale_blend + '.output', jnt + '.scale')
        cmds.connectAttr(reverse + '.outputX', scale_blend + '.blender')

def ik_stretch_setup(ikh):
    joints = cmds.ikHandle(ikh, q=True, jointList=True)
    end_eff = cmds.ikHandle(ikh, q=True, endEffector=True)

    start_pos = cmds.xform(joints[0], q=True, ws=True, t=True)
    end_pos = cmds.xform(end_eff, q=True, ws=True, t=True)

    dist_shape = cmds.distanceDimension(sp=start_pos, ep=end_pos)

    orig_dist = cmds.getAttr(joints[1] + '.tx') + cmds.getAttr(end_eff + '.tx')

    div = cmds.createNode('divide', name=ikh + '_stretchDiv')
    cmds.setAttr(div + '.input2', orig_dist)
    cmds.connectAttr(dist_shape + '.distance', div + '.input1')

    clamp = cmds.createNode('clamp')
    cmds.setAttr(clamp + '.minR', 1)
    cmds.setAttr(clamp + '.maxR', 10)
    cmds.connectAttr(div + '.output', clamp + '.inputR')

    cmds.connectAttr(clamp + '.outputR', joints[0] + '.sx')
    cmds.connectAttr(clamp + '.outputR', joints[1] + '.sx')

    sq_div = cmds.createNode('divide', name=ikh + '_sqDiv')
    pow = cmds.createNode('power', name=ikh + '_sqPow')
    cmds.setAttr(pow + '.exponent', .5)
    cmds.setAttr(sq_div + '.input1', 1)
    cmds.connectAttr(pow + '.output', sq_div + '.input2')
    cmds.connectAttr(clamp + '.outputR', pow + '.input')

    for jnt in joints:
        cmds.connectAttr(sq_div + '.output', jnt + '.sy')
        cmds.connectAttr(sq_div + '.output', jnt + '.sz')


def rig_tool_window():
    if cmds.window('rigToolWindow', exists=True):
        cmds.deleteUI('rigToolWindow')

    win = cmds.window('rigToolWindow', title='FK IK Rig', widthHeight=(300, 250))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=('both', 10))

    cmds.separator(height=10)
    cmds.text(label='FK IK Rig Tools', font='boldLabelFont')
    cmds.separator(height=10)

    cmds.button(label='Duplicate Chain',     command=lambda x: duplicate_chain())
    cmds.button(label='Create FK Controls', command=lambda x: create_fk_controls())
    cmds.button(label='Create IK Setup',     command=lambda x: ik_control_setup())
    cmds.button(label='Create FK IK Switch', command=lambda x: create_fk_ik_switch())
    cmds.button(label='IK Stretch Setup',    command=lambda x: ik_stretch_setup('L_arm_IKH'))

    cmds.separator(height=10)
    cmds.showWindow(win)




rig_tool_window()