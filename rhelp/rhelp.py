from typing import Union, Optional, Any

import discord
from discord.ext import commands

from core import checks
from cogs.utility import PermissionLevel

from bot import ModmailBot

class Rhelp(commands.Cog):
    def __init__(self, bot: ModmailBot):
        self.bot = bot

    async def get_command_signature(self, command, context):
        parent: Optional[commands.Group[Any, ..., Any]] = command.parent  # type: ignore # the parent will be a Group
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + ' ' + parent.signature)
            parent = parent.parent  # type: ignore
        parent_sig = ' '.join(reversed(entries))

        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent_sig:
                fmt = parent_sig + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + ' ' + command.name

        return f'{context.clean_prefix}{alias} {command.signature}'
    
    async def filter_commands(self, group_commands, ctx):
        key = lambda c: c.name

        iterator = filter(lambda c: not c.hidden, group_commands)

        ret = []
        for cmd in iterator:
            ret.append(cmd)

        return ret

    async def get_help_embed(self, command: Union[commands.Command, commands.Group], ctx) -> discord.Embed:
        embed = None
        signature = await self.get_command_signature(command, ctx)
        perm_level = ctx.bot.command_perm(command.qualified_name)
        if perm_level is not PermissionLevel.INVALID:
            perm_level = f"{perm_level.name} [{perm_level}]"
        else:
            perm_level = "NONE"

        embed = discord.Embed(
            title=f'{signature.strip()}',
            description=command.help or 'No Description.',
            color=ctx.bot.main_color
        )
        if isinstance(command, commands.Group):
            embed.add_field(name='Permission Level', value=perm_level, inline=False)

            format_ = ""
            length = len(command.commands)

            for i, command in enumerate(
                await self.filter_commands(command.commands, ctx)
                ):
            # BUG: fmt may run over the embed limit
            # TODO: paginate this
                if length == i + 1:  # last
                    branch = "└─"
                else:
                    branch = "├─"
                format_ += f"`{branch} {command.name}` - {command.short_doc}\n"
            
            embed.add_field(name=f'Sub Command(s)', value=f'{format_}')
        else:
            embed.set_footer(text=f'Permission level: {perm_level}')
        return embed

    @commands.command(name='rhelp')
    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def rhelp(self, ctx: commands.Context, *, command: str):
        bot_command = self.bot.get_command(command)
        if not bot_command:
            return await ctx.send(f'Bot Command `{command}` not found.')
        help_embed = await self.get_help_embed(bot_command, ctx)
        help_embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        try:
            await ctx.thread.recipient.send(embed=help_embed)
            await ctx.send(f'Command help for `{command}` sent to the user.')
        except Exception:
            await ctx.send(f'The command help could not get sent to the user.')

    @commands.command(name='arhelp')
    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def arhelp(self, ctx: commands.Context, *, command: str):
        bot_command = self.bot.get_command(command)
        if not bot_command:
            return await ctx.send(f'Bot Command `{command}` not found.')
        help_embed = await self.get_help_embed(bot_command, ctx)
        help_embed.set_author(name='Modmail Support Agent', icon_url='https://discordapp.com/assets/f78426a064bc9dd24847519259bc42af.png')
        try:
            await ctx.thread.recipient.send(embed=help_embed)
            await ctx.send(f'Command help for `{command}` sent to the user.')
        except Exception:
            await ctx.send(f'The command help could not get sent to the user.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Rhelp(bot))
