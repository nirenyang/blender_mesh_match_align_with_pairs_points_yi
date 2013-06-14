# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#
# mesh_match_align_with_pairs_points_yi.py

bl_info = {
    'name': "Points Pairs Align / Match",
    'description': "A Aligner / Matcher with your selected 1-3 Points Pairs from two Meshes",
    'author': "Yi Danyang( BeiJing DynastyGroup )",
    'version': ( 0, 0, 2 ),
    'blender': ( 2, 6, 4, 9 ),
    'api': 52422,
    'location': '3D View -> Mesh Tools -> Points Pairs Align / Match  OR  in [ Mesh Edit mode ] w-key',
    'warning': "Alpha",
    'category': 'Mesh',
    "wiki_url": "mailto:yidanyang@gmail.com",
    "tracker_url": "mailto:yidanyang@gmail.com",
}




#必要模块引用
import bpy
# from math import radians #degrees #, sqrt
from math import pi
import mathutils
# from mathutils import Vector
from bpy.props import EnumProperty, BoolProperty, IntProperty


class PointsPairsAlignMatch( bpy.types.Operator ):
    
    #匹配方法
    bl_idname = "mesh.points_pairs_align_match"
    bl_label = "Points Pairs Align / Match"
    bl_description = "Points Pairs Align / Match"
    bl_options = {'REGISTER', 'UNDO'}
    
    BoolTranslate = BoolProperty( name='Translate', description='Translate', default=True )
    BoolTranslateCenter = BoolProperty( name='Center', description='Center', default=False )
    BoolTranslateCenterTmp = False
    StaticTransformIndex = IntProperty( name='Static', description='Index', default=0, min=0, max=2 )
    DynamicTransformIndex = IntProperty( name='Dynamic', description='Index', default=0, min=0, max=2 )
    
    BoolRotate = BoolProperty( name='Rotate', description='Rotate', default=True )
    BoolRotate1Flip = BoolProperty( name='Flip', description='Flip', default=True )
    BoolScale = BoolProperty( name='Scale', description='Scale', default=False )
    StaticScaleIndex = IntProperty( name='Index', description='Index', default=0, min=0, max=2 )
    
    objs = vts = pairs = matrix = None
        
    @classmethod
    def poll( cls, context ):
        obj = context.active_object
        return ( obj and obj.type == 'MESH' )
        
    #显示operater
    def draw( self, context ):
        #如果使用text=""，会替换最初定义的按钮名称
        layout = self.layout

        if len( self.objs )>2:
            #多物体匹配模式
            row = layout.row(  )
            row.label( 'Modes : Developing...' )
            row = layout.row(  )
            row.prop( self, 'EnumMode' )
            row.prop( self, 'BoolAngleMatch' )
        row = layout.row(  )
        row.label( 'Options' )
        
        row = layout.row(  )
        
        row.prop( self, 'BoolTranslate' )
        if self.BoolTranslate == True and self.pairs > 1:
            if self.pairs > 2:
                row.prop( self, 'BoolTranslateCenter' )
            if self.BoolTranslateCenter == False:
                row = layout.row( align=True )
                row.prop( self, 'StaticTransformIndex' )
                row.prop( self, 'DynamicTransformIndex' )
        
        if self.pairs > 1:
            row = layout.row(  )
            row.prop( self, 'BoolScale' )
            if self.BoolScale == True and self.pairs > 2:
                row.prop( self, 'StaticScaleIndex' )
            row = layout.row(  )
            
        if self.pairs == 1 or self.BoolTranslate == True:
            row.prop( self, 'BoolRotate' )
            if self.pairs != 2 and self.BoolRotate == True:
                row.prop( self, 'BoolRotate1Flip' )
        layout.separator(  )

        
####################################################################################

    def TranslateO( self, context, sObj, sID, dObj, dID ):
        """匹配两个物体的位置"""

        #点对点或者点对中心
        if self.BoolTranslateCenterTmp == False:
            #局部坐标转全局
            wm = sObj.matrix_world.copy()
            sP = wm * (sObj.data.vertices[self.vts[0][sID]].co.copy())
            wm = dObj.matrix_world.copy()
            dP = wm * (dObj.data.vertices[self.vts[self.objs.index(dObj)][dID]].co.copy())
            
            #长度测试
            if (sP - dP).magnitude < 0.000001:
                return
            
            #点点
            dObj.location += (sP - dP)
            # bpy.ops.transform.translate(value=sP - dP)
        else:
            self.BoolTranslateCenterTmp = False
            sIDs = self.IntID(sID)
            dIDs = self.IntID(dID)
            fuc = lambda ob, index, IDs : ob.data.vertices[self.vts[index][IDs[0]]].co.copy() + ob.data.vertices[self.vts[index][IDs[1]]].co.copy() + ob.data.vertices[self.vts[index][IDs[2]]].co.copy()
            sAll = fuc(sObj, 0, sIDs)/3
            dAll = fuc(dObj, self.objs.index(dObj), dIDs)/3
            sWm = sObj.matrix_world.copy()
            dWm = dObj.matrix_world.copy()
            sCs = sWm * sAll
            dCs = dWm * dAll
            if (sCs - dCs).magnitude < 0.000001:
                return
            dObj.location += (sCs - dCs)

        return
        
####################################################################################

    def RotateO( self, context, sObj, sID, dObj, dID ):
        """匹配两个物体的角度"""
        #Crash Why???#
        
        #选择
        if self.pairs == 1: #一点法线
            self.MatchNormals(context, sObj, sID, dObj, dID)
        elif self.pairs > 1:
            sIDs = self.IntID(sID)
            dIDs = self.IntID(dID)
            if self.pairs == 2:
                #两点法线
                self.MatchPair(context, sObj, sIDs, dObj, dIDs)
            elif self.pairs == 3:
                #面中心
                self.MatchPair(context, sObj, sIDs, dObj, dIDs)
                self.MatchPairByPerpendicular(context, sObj, sIDs, dObj, dIDs)
                self.MatchPairByPerpendicular(context, sObj, (sIDs[2],sIDs[1],sIDs[0]), dObj, (dIDs[2],dIDs[1],dIDs[0]))
                if self.BoolTranslateCenter == True:
                    self.BoolTranslateCenterTmp = True
                    self.TranslateO( context, self.objs[0], self.StaticTransformIndex, self.objs[1], self.DynamicTransformIndex )
                    
        else:
            self.MatchNormals(context, sObj, sID, dObj, dID)    #留着纠错
        return
    
    def IntID(self, curID):
        #id init
        if self.pairs == 1: #一点法线
            ereID = nextID = 0
        elif self.pairs == 2:   #两点法线
            ereID = nextID = int( not bool(curID) )
        elif self.pairs == 3:   #面法线
            ereID = 2 if curID==0 else curID-1
            nextID = 0 if curID==2 else curID+1
        else:
            self.report( {'WARNING'}, 'Wrong ID has been Ignored' )
            ereID = nextID = 0
        # print('ereID: %s curID: %s nextID: %s' % (ereID, curID, nextID))
        return (ereID, curID, nextID)
    
    def NormalTransformMatrix(self, m):
        m_normal = m.inverted().transposed()
        m_normal[0][3] = 0.0
        m_normal[1][3] = 0.0
        m_normal[2][3] = 0.0
        return m_normal
        
    def MatchNormals(self, context, sObj, sID, dObj, dID):
        """
        以法线为依据旋转
        """
        #角度相关
        wm = self.NormalTransformMatrix(sObj.matrix_world.copy())
        sNor = (wm * (sObj.data.vertices[self.vts[0][sID]].normal.copy())).normalized()
        wm = self.NormalTransformMatrix(dObj.matrix_world.copy())
        dNor = (wm * (dObj.data.vertices[self.vts[self.objs.index(dObj)][dID]].normal.copy())).normalized()
        
        angle = sNor.angle(dNor)
        if angle<0.000001:
            return
        cross = sNor.cross(dNor)
        cross = dNor.cross(sNor)
        if self.pairs == 1:
            if self.BoolRotate1Flip == True:
                angle += pi
            angle *= -1
            
        bpy.ops.transform.rotate(value=angle, axis=cross)
        return
    
    def MatchPair(self, context, sObj, sID, dObj, dID):
        #旋转中心
        #传入ID并不是len==3，而是len==2
        wm = dObj.matrix_world.copy()
        dP1 = wm * (dObj.data.vertices[self.vts[self.objs.index(dObj)][dID[1]]].co.copy())
        dP2 = wm * (dObj.data.vertices[self.vts[self.objs.index(dObj)][dID[2]]].co.copy())
        dVct = (dP1 - dP2).normalized()
        
        wm = sObj.matrix_world.copy()
        sP1 = wm * (sObj.data.vertices[self.vts[0][sID[1]]].co.copy())
        sP2 = wm * (sObj.data.vertices[self.vts[0][sID[2]]].co.copy())
        sVct = (sP1 - sP2).normalized()
        
        #角度相关
        angle = dVct.angle(sVct)
        if angle < 0.000001:
            return
            
        cross = dVct.cross(sVct)
        
        bpy.ops.transform.rotate(value=angle, axis=cross)
        return
    
    def MatchPairByPerpendicular(self, context, sObj, sID, dObj, dID):
        #当互相垂直角度不为90度时，使用这个
        #我们现在已有一条公共边与两个可能与垂直与公共边的面异面的点，如果两点到公共边上的最小距离坐标很近，说明两个三角形是镜像关系；
        #这是MatchPair的升级版，但是最好先用MatchPair得到公共边，容易理解
        
        #通过RotateO的判断，我们已经将三对[0-1-2]的[1-2]进行了公共边处理，所以，0是可能是与垂直与公共边的面异面的点。
        #所以，几乎可以忽视部分传入参数,eg : ID
        
        if len(sID) != 3 or len(dID) != 3:
            self.report( {'WARNING'}, 'Perpendicular Error in MatchPairByPerpendicular Function!!!' )
            return
            
        #两点
        wm = sObj.matrix_world.copy()
        sP0 = wm * (sObj.data.vertices[self.vts[0][sID[0]]].co.copy())
        wm = dObj.matrix_world.copy()
        dP0 = wm * (dObj.data.vertices[self.vts[self.objs.index(dObj)][dID[0]]].co.copy())
        
        #两点是否重合
        if (dP0 - sP0).magnitude < 0.000001:
            return
        
        #公共边
        wm = sObj.matrix_world.copy()
        sP1 = wm * (sObj.data.vertices[self.vts[0][sID[1]]].co.copy())
        sP2 = wm * (sObj.data.vertices[self.vts[0][sID[2]]].co.copy())
        
        #映射点，求矢量-角度
        from mathutils import geometry
        sP4 = geometry.intersect_point_line(sP0, sP1, sP2)[0]
        dP4 = geometry.intersect_point_line(dP0, sP1, sP2)[0]
        v1, v2 = (sP4 - sP0).normalized(), (dP4 - dP0).normalized()
        
        #角度相关
        angle = v1.angle(v2)
        if angle < 0.000001:
            return
            
        cross = v1.cross(v2)
        
        if self.BoolRotate1Flip == True:
            angle += pi
        angle *= -1
            
        bpy.ops.transform.rotate(value=angle, axis=cross)
        return
        
####################################################################################

    def ScaleO( self, context, sObj, sID, dObj, dID ):
        """匹配两个物体的大小"""
        dst = lambda x,y : (x-y).magnitude
        sIDs = self.IntID(sID)
        dIDs = self.IntID(dID)

        if self.pairs == 1:
            return
        elif self.pairs == 2:
            dP1 = dObj.data.vertices[self.vts[self.objs.index(dObj)] [dIDs[0]]].co.copy()
            dP2 = dObj.data.vertices[self.vts[self.objs.index(dObj)] [dIDs[1]]].co.copy()
            sP1 = sObj.data.vertices[self.vts[0] [sIDs[0]]].co.copy()
            sP2 = sObj.data.vertices[self.vts[0] [sIDs[1]]].co.copy()
        elif self.pairs == 3:
            sIndex = self.IntID(self.StaticScaleIndex)
            print(sIndex)
            dP1 = dObj.data.vertices[self.vts[self.objs.index(dObj)] [dIDs[sIndex[0]]] ].co.copy()
            dP2 = dObj.data.vertices[self.vts[self.objs.index(dObj)] [dIDs[sIndex[1]]] ].co.copy()
            sP1 = sObj.data.vertices[self.vts[0] [ sIDs[ sIndex[0] ] ] ].co.copy()
            sP2 = sObj.data.vertices[self.vts[0] [ sIDs[ sIndex[1] ] ] ].co.copy()
        
        wm = sObj.matrix_world.copy()
        sDst = dst( wm * sP1, wm * sP2 )
        wm = dObj.matrix_world.copy()
        dDst = dst( wm * dP1, wm * dP2 )
        
        if abs(sDst-dDst)<0.000001:
            return
            
        #缩放
        bpy.ops.transform.resize(value=(sDst/dDst,)*3)
        return
        
####################################################################################   
####################################################################################

    def execute( self, context ):
        #Object
        bpy.ops.object.mode_set( mode='OBJECT' )

        #数据合法性
        if not self.Check( context ):
            return {'CANCELLED'}
        
        #还原矩阵 -- 不记得为什么要这样做了...好像是为了修改参数时，不是继续计算而是重新计算
        if not self.matrix == None:
            for i in range( len( self.matrix ) ):
                self.objs[i].matrix_world = self.matrix[i]
 
        if len( self.objs )<3:
            if context.active_object != self.objs[1]:
                bpy.ops.object.select_all(action='DESELECT')
                context.scene.objects.active = self.objs[1]
                self.objs[1].select = True

            if self.BoolTranslate == True:
                self.TranslateO( context, self.objs[0], self.StaticTransformIndex, self.objs[1], self.DynamicTransformIndex )
            if self.BoolRotate == True:
                self.RotateO( context, self.objs[0], self.StaticTransformIndex, self.objs[1], self.DynamicTransformIndex )
            if self.BoolScale == True:
                self.ScaleO( context, self.objs[0], self.StaticTransformIndex, self.objs[1], self.DynamicTransformIndex )

        #还原
        self.Outer( context )
        return {'FINISHED'}


    def Check( self, context ):
        if len( context.selected_objects ) < 2:
            self.report( {'WARNING'}, 'Need 2 Selected Valid Meshes at least!' )
            return False
            
        #所有有效模型
        tmp = [i for i in context.selected_objects if i.type == 'MESH']
        #再迭代一次，每个选中的至少一个点，否则out
        for i in tmp[:]:
            # if i.data.total_vert_sel == 0:    #为什么全都是0呢，上次还不是这样的
            if len( [x for x in i.data.vertices if x.select == True] ) == 0:
                tmp.remove( i )
                
        #至少需要两个有效模型      
        if len( tmp ) < 2:
            self.report( {'WARNING'}, 'Need 2 Selected Valid Meshes at least!' )
            return False
            
        #objs[0]是激活的固定模型，其他都是选择的
        #多个物体对齐
        self.objs = [context.active_object,]
        tmp.remove( self.objs[0] )
        self.objs.extend(  tmp  )
        
        #基准数量
        self.pairs = len( [x for x in self.objs[0].data.vertices if x.select == True] )   #self.objs[0].data.total_vert_sel #为什么全都是0呢，上次还不是这样的
        
        #StaticTransformIndex默认范围0～2，三位，但现在想应用到选择两点时，所以需要在某个情况下修正一下
        if self.pairs == 1:
            #由于Blender会储存上次参数，所以在1 pair时需要修正，否则，3之后，1、2都废了
            self.StaticTransformIndex = 0
            self.DynamicTransformIndex = 0
            self.StaticScaleIndex = 0
        elif self.pairs == 2:
            if self.StaticTransformIndex == 2:
                self.StaticTransformIndex = 1
            if self.DynamicTransformIndex == 2:
                self.DynamicTransformIndex = 1
            if self.StaticScaleIndex == 2:
                self.StaticScaleIndex = 1

        #顶点包- 选择顶点的集合 [ ob[p,p], ob[p,p], ...]
        self.vts = [[i.index for i in m.data.vertices if i.select == True] for m in self.objs]
        
        #动态模型的选择点绝对不能比静态物体选择的点少，不然，程序里要做很多判断，不管怎么样，先这么样了
        removed = ''
        cpObj = self.objs[:]
        cpVts = self.vts[:]
        for i in range(len(self.vts)):
            #print('%s %s' % (len(self.vts[i]), self.pairs))
            if len(self.vts[i]) < self.pairs:
                removed = removed + self.objs[i].name + ' , '
                cpObj.remove(self.objs[i])
                cpVts.remove(self.vts[i])
        if removed != '':
            print('\nIgnore Meshes：\n%s\n' % removed)
            self.report( {'WARNING'}, 'Check the Ignore Mesh list in System Console ... Ignore Meshes' )
        if len(cpObj)<1 or len(cpVts)<1:
            self.report( {'WARNING'}, 'Mesh or Selected Element count Invalid' )
            return False
            
        self.objs = cpObj
        self.vts = cpVts
        
        #漏网之鱼，再次过滤
        if len(self.objs) < 2:
            self.report( {'WARNING'}, 'Valid Meshes is less than 2' )
            return False
        
        #矩阵备份
        if self.matrix == None:
            self.matrix = [i.matrix_world.copy(  ) for i in self.objs]
        
        self.objs = tuple( self.objs )
        
        #点模式
        context.tool_settings.mesh_select_mode = (True, False, False)
        #模型状态  - 动态模型被激活
        bpy.ops.object.select_all(action='DESELECT')
        context.scene.objects.active = self.objs[1]
        self.objs[1].select = True
        
        #逻辑修复  
        if self.pairs == 3:
            #中心移动临时方案
            # if self.BoolTranslateCenter == True:
                # self.BoolTranslateCenterTmp = True
            if self.BoolTranslate == False:
                self.BoolRotate = False
        else:
            self.BoolTranslateCenter == False
            
        #中心
        wm = self.objs[1].matrix_world.copy()
        dP = wm * (self.objs[1].data.vertices[self.vts[1][self.DynamicTransformIndex]].co.copy())
        if context.scene.cursor_location != dP:
            context.scene.cursor_location = dP
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        return True
  
    def Outer( self, context ):
        bpy.ops.object.mode_set( mode='OBJECT' )
        bpy.ops.object.select_all( action='DESELECT' )
        context.scene.objects.active = self.objs[0]
        for x in self.objs:
            x.select=True
        
        #以防万一，更容易看懂，移动到哪里了
        wm = self.objs[1].matrix_world.copy()
        dP = wm * (self.objs[1].data.vertices[self.vts[1][self.DynamicTransformIndex]].co.copy() )
        if context.scene.cursor_location != dP:
            context.scene.cursor_location = dP
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            
        bpy.ops.object.mode_set( mode='EDIT' )
        return
        
    

################################################################################################

#菜单内容
#似乎从这里点击invoke方法无法运行，无法初始化，为什么？只好注释掉了，省得w里太乱
def menu_func( self, context ):
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"
    layout.separator(  )
    layout.operator( PointsPairsAlignMatch.bl_idname , 'Points Pairs Align / Match')

    
#面板内容
# def panel_func( self, context ):
    # layout = self.layout
    # layout.separator(  )
    # layout.label( text="Points Pairs Align / Match:" )
    # layout.operator( PointsPairsAlignMatch.bl_idname, langDic[0] )
    # layout.separator(  )

    
#注册面板与菜单
def register(  ):
    bpy.utils.register_class( PointsPairsAlignMatch )
    
    bpy.types.VIEW3D_PT_tools_meshedit.append( menu_func )
    bpy.types.VIEW3D_MT_edit_mesh_specials.append( menu_func )

    
#卸载面板与菜单
def unregister(  ):
    bpy.utils.unregister_class( PointsPairsAlignMatch )
    
    bpy.types.VIEW3D_PT_tools_meshedit.remove( menu_func )
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove( menu_func )

    
#入口
if __name__ == "__main__":
        register(  )

    #test call
    # bpy.ops.object.PointsPairsAlignMatch()
